from kfp import kubernetes
from kfp import dsl
from kfp import compiler

@dsl.component(base_image="maiacloud/monet-pipeline:1.3")
def create_docker_context(context: str, segmentation_task_file: str, model_file: str):  
    import subprocess

    repo_url = "https://github.com/SimoneBendazzoli93/MONet-Bundle.git"
    clone_dir = "/data/"+context

    subprocess.run(["rm", "-rf", clone_dir], check=True)
    subprocess.run(["git", "clone", repo_url, clone_dir], check=True)
    subprocess.run(["mkdir", "-p", f"{clone_dir}/deploy/monet-x64-workstation-dgpu-linux-amd64/models/model/"], check=True)
    subprocess.run(["cp", "/data/"+segmentation_task_file, f"{clone_dir}/deploy/monet-x64-workstation-dgpu-linux-amd64/Segmentation_Task.yaml"], check=True)
    subprocess.run(["cp", "/data/"+model_file, f"{clone_dir}/deploy/monet-x64-workstation-dgpu-linux-amd64/models/model/model.ts"], check=True)
    subprocess.run(["mkdir", "-p", f"{clone_dir}/deploy/monet-x64-workstation-dgpu-linux-amd64-nifti/models/model/"], check=True)
    subprocess.run(["cp", "/data/"+segmentation_task_file, f"{clone_dir}/deploy/monet-x64-workstation-dgpu-linux-amd64-nifti/Segmentation_Task.yaml"], check=True)
    subprocess.run(["cp", "/data/"+model_file, f"{clone_dir}/deploy/monet-x64-workstation-dgpu-linux-amd64-nifti/models/model/model.ts"], check=True)



@dsl.container_component
def build_docker_image(context: str, destination: str):    
    return dsl.ContainerSpec(
        image='gcr.io/kaniko-project/executor:latest',
        command=[
            "/kaniko/executor",
            "--dockerfile=Dockerfile",
            f"--context=/data/{context}/deploy/monet-x64-workstation-dgpu-linux-amd64",
            f"--destination={destination}",
            "--build-arg",
            "UID=1000",
            "--build-arg",
            "GID=1000",
            "--build-arg",
            "UNAME=holoscan",
            "--build-arg",
            "GPU_TYPE=dgpu",
        ],
    )

@dsl.container_component
def build_docker_image_nifti(context: str, destination: str):    
    return dsl.ContainerSpec(
        image='gcr.io/kaniko-project/executor:latest',
        command=[
            "/kaniko/executor",
            "--dockerfile=Dockerfile",
            f"--context=/data/{context}/deploy/monet-x64-workstation-dgpu-linux-amd64-nifti",
            f"--destination={destination}",
            "--build-arg",
            "UID=1000",
            "--build-arg",
            "GID=1000",
            "--build-arg",
            "UNAME=holoscan",
            "--build-arg",
            "GPU_TYPE=dgpu",
        ],
    )


@dsl.pipeline(
    name="Docker Build Pipeline",
    description="Pipeline that builds Docker image using Kaniko."
)
def docker_build_pipeline(context: str, destination: str, destination_nifti: str, segmentation_task_file: str, model_file: str):
    task0 = create_docker_context(context=context, segmentation_task_file=segmentation_task_file, model_file=model_file).set_cpu_request('1000m').set_cpu_limit('2000m').set_memory_request('8Gi').set_memory_limit('8Gi')
    
    kubernetes.mount_pvc(
        task0,
        pvc_name='shared',
        mount_path='/data',
    )
    # Create task to build docker image
    task1 = build_docker_image(context=context, destination=destination).set_cpu_request('1000m').set_cpu_limit('2000m').set_memory_request('24Gi').set_memory_limit('24Gi').after(task0)

    # Use Dockerhub secrets to pull the image
    kubernetes.set_image_pull_secrets(task1, secret_names=["maiacloud-dockerhub"])
    
    # Mount secret as volume for Kaniko credentials
    kubernetes.use_secret_as_volume(task1, "maiacloud-dockerhub", "/kaniko/.docker")
        
    # Mount PVC to provide shared data
    kubernetes.mount_pvc(
        task1,
        pvc_name='shared',
        mount_path='/data',
    )
    
    task2 = build_docker_image_nifti(context=context, destination=destination_nifti).set_cpu_request('1000m').set_cpu_limit('2000m').set_memory_request('24Gi').set_memory_limit('24Gi').after(task0)
    # Use Dockerhub secrets to pull the image
    kubernetes.set_image_pull_secrets(task2, secret_names=["maiacloud-dockerhub"])
    # Mount secret as volume for Kaniko credentials
    kubernetes.use_secret_as_volume(task2, "maiacloud-dockerhub", "/kaniko/.docker")
    # Mount PVC to provide shared data
    kubernetes.mount_pvc(
        task2,
        pvc_name='shared',
        mount_path='/data',
    )


# Compile the pipeline to generate YAML
compiler.Compiler().compile(docker_build_pipeline, package_path='Docker_Build_pipeline.yaml')