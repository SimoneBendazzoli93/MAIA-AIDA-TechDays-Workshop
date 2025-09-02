from kfp import kubernetes
from kfp import dsl
from kfp import compiler


@dsl.component(base_image="maiacloud/monet-pipeline:1.3-monailabel")
def dicom_to_nifti(studies: str, output_folder: str):
    from monailabel.datastore.dicom import DICOMWebDatastore, DICOMwebClientX
    from dicomweb_client.session_utils import create_session_from_user_pass
    import SimpleITK as sitk
    from pydicom.dataset import Dataset
    from pathlib import Path
    import nibabel as nib
    from nilearn.image import resample_to_img
    from monailabel.config import settings


    dw_session = create_session_from_user_pass(
                        settings.MONAI_LABEL_DICOMWEB_USERNAME, settings.MONAI_LABEL_DICOMWEB_PASSWORD
                    )

    dw_client = DICOMwebClientX(
                    url=studies,
                    session=dw_session,
                    qido_url_prefix=settings.MONAI_LABEL_QIDO_PREFIX,
                    wado_url_prefix=settings.MONAI_LABEL_WADO_PREFIX,
                    stow_url_prefix=settings.MONAI_LABEL_STOW_PREFIX,
                )

    cache_path = settings.MONAI_LABEL_DICOMWEB_CACHE_PATH
    cache_path = cache_path.strip() if cache_path else ""
    fetch_by_frame = settings.MONAI_LABEL_DICOMWEB_FETCH_BY_FRAME
    search_filter = settings.MONAI_LABEL_DICOMWEB_SEARCH_FILTER
    convert_to_nifti = settings.MONAI_LABEL_DICOMWEB_CONVERT_TO_NIFTI

    datastore = DICOMWebDatastore(
                client=dw_client,
                search_filter=search_filter,
                cache_path=cache_path if cache_path else None,
                fetch_by_frame=fetch_by_frame,
                convert_to_nifti=convert_to_nifti,
            )

    datalist = datastore.datalist()

    print(f"Total Studies: {len(datalist)}")

    Path(output_folder).mkdir(parents=True, exist_ok=True)
    for data in datalist:
        image = data["image"]
        img = sitk.ReadImage(image)
        study_id = Path(image).name[:-len(".nii.gz")]

        # Find PatientID from StudyInstanceUID
        study_list = dw_client.search_for_studies(search_filters={"StudyInstanceUID": study_id})

        if study_list:
            meta = Dataset.from_json(study_list[0])
            patient_id = str(meta.get("PatientID", "Unknown"))
        else:
            patient_id = "Unknown"
        Path(output_folder).joinpath(patient_id).mkdir(parents=True, exist_ok=True)
        sitk.WriteImage(img, Path(output_folder).joinpath(patient_id, f"{patient_id}_image.nii.gz"))

        label = data["label"]
        lbl = sitk.ReadImage(label)
        sitk.WriteImage(lbl, Path(output_folder).joinpath(patient_id, f"{patient_id}_label.nii.gz"))
        input_image = nib.load(Path(output_folder).joinpath(patient_id, f"{patient_id}_label.nii.gz"))
        reference_image = nib.load(Path(output_folder).joinpath(patient_id, f"{patient_id}_image.nii.gz"))
        resampled_image = resample_to_img(input_image, reference_image, interpolation="nearest", fill_value=0)
        nib.save(resampled_image, Path(output_folder).joinpath(patient_id, f"{patient_id}_label.nii.gz"))


@dsl.pipeline(
    name="DICOM to NIFTI from Orthanc Pipeline",
    description="Pipeline to convert DICOM images to NIFTI format from Orthanc Instance."
)
def dicom_to_nifti_pipeline(studies: str, output_folder: str):
    # Create task to build docker image
    task1 = dicom_to_nifti(studies=studies, output_folder=output_folder).set_caching_options(False).set_cpu_request('1000m').set_cpu_limit('8000m').set_memory_request('8Gi').set_memory_limit('32Gi')#.set_accelerator_type("nvidia.com/gpu")

    # Use Dockerhub secrets to pull the image
    #kubernetes.set_image_pull_secrets(task1, secret_names=["maia-cloud-ai-registry"])
    
    # Mount secret as volume for Kaniko credentials
    #kubernetes.use_secret_as_volume(task1, "maia-cloud-ai-registry", "/kaniko/.docker")

    # Mount PVC to provide shared data
    kubernetes.mount_pvc(
        task1,
        pvc_name='shared',
        mount_path='/mnt/Data',
    )

    kubernetes.add_ephemeral_volume(task1, mount_path='/dev/shm', volume_name='shm', access_modes=['ReadWriteOnce'], size='2Gi',storage_class_name='local-path')



compiler.Compiler().compile(dicom_to_nifti_pipeline, package_path='DICOM_to_NIFTI_pipeline.yaml')