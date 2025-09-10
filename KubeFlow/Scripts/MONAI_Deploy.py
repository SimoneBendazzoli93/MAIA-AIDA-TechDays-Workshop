from kfp import kubernetes
from kfp import dsl
from kfp import compiler





@dsl.container_component
def spleen_segmentation(holo_input: str, holo_output: str, image: str):    
    return dsl.ContainerSpec(
        image=str(image),
        command=["bash", "-c"],
        args=[
            "export HOLOSCAN_INPUT_PATH=$0 && export HOLOSCAN_OUTPUT_PATH=$1 && python3 /opt/holoscan/app",
            "/var/holoscan/"+str(holo_input),
            "/var/holoscan/"+str(holo_output)
        ]
    )
    

@dsl.pipeline(
    name="MONet Inference Pipeline",
    description="Pipeline that runs the MONet Inference."
)
def monet_inference_pipeline(input_folder_path: str, output_folder_path: str, image: str):
    # Create task to build docker image
    task1 = spleen_segmentation(holo_input=input_folder_path, holo_output=output_folder_path, image=image).set_caching_options(False).set_cpu_request('1000m').set_cpu_limit('8000m').set_memory_request('8Gi').set_memory_limit('16Gi').set_accelerator_type("nvidia.com/gpu").set_env_variable("SEGMENTATION_TASK_CONFIG_FILE", "/etc/holoscan/Segmentation_Task.yaml").set_env_variable("SEGMENTATION_TASK_NAME", "Spleen")

    kubernetes.add_node_selector(task1, "kubernetes.io/hostname", "maia-small-5")
    # Mount PVC to provide shared data
    kubernetes.mount_pvc(
        task1,
        pvc_name='shared',
        mount_path='/var/holoscan',
    )

    kubernetes.add_ephemeral_volume(task1, mount_path='/dev/shm', volume_name='shm', access_modes=['ReadWriteOnce'], size='2Gi',storage_class_name='local-path')
    
    
compiler.Compiler().compile(monet_inference_pipeline, package_path='MONet_Inference_pipeline.yaml')