from kfp import kubernetes
from kfp import dsl
from kfp import compiler

@dsl.component(packages_to_install=['pytorch-ignite','SimpleITK','nibabel'],base_image="maiacloud/monet-pipeline:1.3")
def download_decathlon_dataset(decathlon_task: str):
    import os
    from monai.apps import DecathlonDataset
    os.environ["MONAI_DATA_DIRECTORY"] = "/mnt/Data"
    root_dir = os.environ.get("MONAI_DATA_DIRECTORY")
    DecathlonDataset(root_dir=root_dir, task=decathlon_task, section="training", download=True, cache_num=1)
    root_folder = os.path.join(root_dir, decathlon_task)
    for dirpath, dirnames, filenames in os.walk(root_folder):
        for filename in filenames:
            if filename.startswith('.'):
                full_path = os.path.join(dirpath, filename)
                try:
                    os.remove(full_path)
                    print(f"Deleted: {full_path}")
                except Exception as e:
                    print(f"Failed to delete {full_path}: {e}")




@dsl.pipeline(
    name="Decathlon Dataset Pipeline",
    description="Pipeline to download the requested Decathlon dataset."
)
def decathlon_dataset_pipeline(decathlon_task: str):
    # Create task to build docker image
    task1 = download_decathlon_dataset(decathlon_task=decathlon_task).set_caching_options(False).set_cpu_request('1000m').set_cpu_limit('8000m').set_memory_request('8Gi').set_memory_limit('32Gi')#.set_accelerator_type("nvidia.com/gpu")
   
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



compiler.Compiler().compile(decathlon_dataset_pipeline, package_path='Decathlon_Dataset_pipeline.yaml')