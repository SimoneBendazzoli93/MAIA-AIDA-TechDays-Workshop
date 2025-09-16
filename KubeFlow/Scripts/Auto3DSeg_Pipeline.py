from kfp import kubernetes
from kfp import dsl
from kfp import compiler

@dsl.component(packages_to_install=['pytorch-ignite','odict','fire','SimpleITK','nibabel','monai'],base_image="maiacloud/monet-pipeline:1.3")
def auto3dseg(config_file_path: str):    
    import time
    import subprocess

    start = time.time()
    subprocess.run([
        "python3", "-m", "monai.apps.auto3dseg", "AutoRunner", "run",
        f"--input=/mnt/Data/{config_file_path}",
        f"--mlflow_tracking_uri=https://mlflow.fed-lymphoma.maia-small.se"
    ])

    end = time.time()
    print(f"Elapsed time: {end - start:.1f} seconds")

@dsl.pipeline(
    name="Auto3DSeg Pipeline",
    description="Pipeline that runs the MONAI Auto3DSeg."
)
def auto3dseg_pipeline(config_file_path: str):
    task1 = auto3dseg(config_file_path=config_file_path).set_caching_options(False).set_cpu_request('1000m').set_cpu_limit('8000m').set_memory_request('8Gi').set_memory_limit('32Gi').set_accelerator_type("nvidia.com/gpu").set_env_variable("MLFLOW_TRACKING_URI", "https://mlflow.fed-lymphoma.maia-small.se")

    kubernetes.mount_pvc(
            task1,
            pvc_name='cifs-pvc',
            mount_path='/mnt/Data',
        )
    kubernetes.add_node_selector(task1, "kubernetes.io/hostname", "maia-small-5")
    kubernetes.add_ephemeral_volume(task1, mount_path='/dev/shm', volume_name='shm', access_modes=['ReadWriteOnce'], size='2Gi',storage_class_name='local-path')
    kubernetes.add_ephemeral_volume(task1, mount_path='/opt/work_dir', volume_name='work-dir', access_modes=['ReadWriteOnce'], size='10Gi',storage_class_name='local-path')
