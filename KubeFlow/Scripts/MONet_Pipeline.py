from kfp import kubernetes
from kfp import dsl
from kfp import compiler


@dsl.component(packages_to_install=['pytorch-ignite','SimpleITK','nibabel'],base_image="maiacloud/monet-pipeline:1.3")
def prepare(config_file_path: str):    
    import time
    import os
    import subprocess
    import yaml

    with open("/mnt/Data/"+config_file_path,"r") as f:
        config_dict = yaml.safe_load(f)

    config_dict["steps"] = ["prepare"]

    with open("/tmp/config_prepare.yaml","w") as f:
        yaml.dump(config_dict,f)

    with open("/tmp/config_prepare.yaml","r") as f:
        config_dict = yaml.safe_load(f)
    print(config_dict)

    start = time.time()
    os.environ["PYTHONPATH"]= config_dict["bundle_config"]["bundle_root"]
    subprocess.run(["python3",
                   "MONet_pipeline.py",
                    "--config",
                    "/tmp/config_prepare.yaml"])
    end = time.time()
    print(f"Elapsed time: {end - start:.1f} seconds")

@dsl.component(packages_to_install=['pytorch-ignite','SimpleITK','nibabel'],base_image="maiacloud/monet-pipeline:1.3")
def plan_and_preprocess(config_file_path: str):    
    import time
    import os
    import subprocess
    import yaml

    with open("/mnt/Data/"+config_file_path,"r") as f:
        config_dict = yaml.safe_load(f)

    config_dict["steps"] = ["plan_and_preprocess"]

    with open("/tmp/config_plan_and_preprocess.yaml","w") as f:
        yaml.dump(config_dict,f)

    with open("/tmp/config_plan_and_preprocess.yaml","r") as f:
        config_dict = yaml.safe_load(f)
    print(config_dict)

    start = time.time()
    os.environ["PYTHONPATH"]= config_dict["bundle_config"]["bundle_root"]
    subprocess.run(["python3",
                   "MONet_pipeline",
                    "--config",
                    "/tmp/config_plan_and_preprocess.yaml"])
    end = time.time()
    print(f"Elapsed time: {end - start:.1f} seconds")

@dsl.component(packages_to_install=['pytorch-ignite','SimpleITK','nibabel','monet-bundle'],base_image="maiacloud/monet-pipeline:1.3")
def prepare_bundle(config_file_path: str):    
    import time
    import os
    import subprocess
    import yaml
    from pathlib import Path
    
    with open("/mnt/Data/"+config_file_path,"r") as f:
        config_dict = yaml.safe_load(f)

    config_dict["steps"] = ["prepare_bundle"]

    with open("/tmp/config_prepare_bundle.yaml","w") as f:
        yaml.dump(config_dict,f)

    with open("/tmp/config_prepare_bundle.yaml","r") as f:
        config_dict = yaml.safe_load(f)
    print(config_dict)
    Path(config_dict["bundle_config"]["bundle_root"]).parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(["MONet_fetch_bundle","--bundle_path", Path(config_dict["bundle_config"]["bundle_root"]).parent])
    start = time.time()
    os.environ["PYTHONPATH"]= config_dict["bundle_config"]["bundle_root"]
    subprocess.run(["python3",
                   "MONet_pipeline",
                    "--config",
                    "/tmp/config_prepare_bundle.yaml"])
    end = time.time()
    print(f"Elapsed time: {end - start:.1f} seconds")
    
@dsl.component(packages_to_install=['pytorch-ignite','odict','SimpleITK','nibabel'],base_image="maiacloud/monet-pipeline:1.3")
def train(config_file_path: str):    
    import time
    import os
    import subprocess
    import yaml

    with open("/mnt/Data/"+config_file_path,"r") as f:
        config_dict = yaml.safe_load(f)

    config_dict["steps"] = ["train"]

    with open("/tmp/config_train.yaml","w") as f:
        yaml.dump(config_dict,f)

    with open("/tmp/config_train.yaml","r") as f:
        config_dict = yaml.safe_load(f)
    print(config_dict)

    start = time.time()
    os.environ["PYTHONPATH"]= config_dict["bundle_config"]["bundle_root"]
    subprocess.run(["python3",
                   "MONet_pipeline",
                    "--config",
                    "/tmp/config_train.yaml"])
    end = time.time()
    print(f"Elapsed time: {end - start:.1f} seconds")

@dsl.component(packages_to_install=['pytorch-ignite','SimpleITK','nibabel'],base_image="maiacloud/monet-pipeline:1.3")
def validate(config_file_path: str):    
    import time
    import os
    import subprocess
    import yaml

    with open("/mnt/Data/"+config_file_path,"r") as f:
        config_dict = yaml.safe_load(f)

    config_dict["steps"] = ["validate"]

    with open("/tmp/config_validate.yaml","w") as f:
        yaml.dump(config_dict,f)

    with open("/tmp/config_validate.yaml","r") as f:
        config_dict = yaml.safe_load(f)
    print(config_dict)

    start = time.time()
    os.environ["PYTHONPATH"]= config_dict["bundle_config"]["bundle_root"]
    subprocess.run(["python3",
                   "/opt/pipeline.py",
                    "--config",
                    "/tmp/config_validate.yaml"])
    end = time.time()
    print(f"Elapsed time: {end - start:.1f} seconds")


@dsl.component(packages_to_install=['pytorch-ignite','SimpleITK','nibabel','monet-bundle'],base_image="maiacloud/monet-pipeline:1.4")
def convert_ckpt_to_ts(config_file_path: str):    
    import time
    import os
    import subprocess
    import yaml

    with open("/mnt/Data/"+config_file_path,"r") as f:
        config_dict = yaml.safe_load(f)

    start = time.time()
    subprocess.run(["MONet_convert_ckpt_to_ts",
                   "--bundle_root",
                    config_dict["bundle_config"]["bundle_root"],
                    "--checkpoint_name",
                    "checkpoint_epoch=1000.pt",
                    "--dataset_name_or_id",
                   config_dict["dataset_name_or_id"]])
    end = time.time()
    print(f"Elapsed time: {end - start:.1f} seconds")

@dsl.component(packages_to_install=['pytorch-ignite','SimpleITK','nibabel','monet-bundle'],base_image="maiacloud/monet-pipeline:1.4")
def convert_ckpt_to_pt(config_file_path: str):    
    import os
    import yaml
    import re
    import os
    import torch
    with open("/mnt/Data/"+config_file_path,"r") as f:
            config_dict = yaml.safe_load(f)
    ckpt_dir = os.path.join(config_dict["bundle_config"]["bundle_root"],"models","fold_{}".format(config_dict.get("fold",0)))
    files = os.listdir(ckpt_dir)

    ckpt_files = [f for f in files if f.endswith('.ckpt')]



    for ckpt_file in ckpt_files:
        match = re.match(r'epoch=(\d+)-([a-zA-Z0-9_]+)=([0-9\.]+)\.ckpt', ckpt_file)
        if match:
            print(f"{ckpt_file} matches: epoch={match.group(1)}, metric={match.group(2)}, value={match.group(3)}")
            state_dict = torch.load(os.path.join(ckpt_dir, ckpt_file), map_location=torch.device('cpu'))
            new_state_dict = {}
            new_state_dict["network_weights"] = {}
            for k, v in state_dict['state_dict'].items():
                new_key = k.replace('network._orig_mod.', '')
                new_state_dict["network_weights"][new_key] = v
            new_state_dict["optimizer_state"] = state_dict['optimizer_states'][0]
            new_state_dict["scheduler"] = state_dict['lr_schedulers'][0]
            val_metric = match.group(3)
            torch.save(new_state_dict, os.path.join(ckpt_dir, f"checkpoint_key_metric={val_metric}.pt"))
        else:
            print(f"{ckpt_file} does not match the pattern.")
        match = re.match(r'epoch=(\d+)\.ckpt', ckpt_file)
        if match:
            print(f"{ckpt_file} matches: epoch={match.group(1)}")
            state_dict = torch.load(os.path.join(ckpt_dir, ckpt_file), map_location=torch.device('cpu'))
            new_state_dict = {}
            new_state_dict["network_weights"] = {}
            for k, v in state_dict['state_dict'].items():
                new_key = k.replace('network._orig_mod.', '')
                new_state_dict["network_weights"][new_key] = v
            new_state_dict["optimizer_state"] = state_dict['optimizer_states'][0]
            new_state_dict["scheduler"] = state_dict['lr_schedulers'][0]
            epoch_num = int(match.group(1)) + 1
            torch.save(new_state_dict, os.path.join(ckpt_dir, f"checkpoint_epoch={epoch_num}.pt"))
        else:
            print(f"{ckpt_file} does not match the pattern.")


@dsl.pipeline(
    name="MONet Pipeline Prepare and Preprocessing",
    description="Pipeline that runs the MONet Bundle Data Preparation and Preprocessing."
)
def monet_pipeline_prepare_and_preprocess(config_file_path: str):
    
    task1 = prepare(config_file_path=config_file_path).set_caching_options(False).set_cpu_request('1000m').set_cpu_limit('8000m').set_memory_request('8Gi').set_memory_limit('32Gi')#.set_accelerator_type("nvidia.com/gpu")
    
    task2 = plan_and_preprocess(config_file_path=config_file_path).set_caching_options(False).set_cpu_request('1000m').set_cpu_limit('8000m').set_memory_request('8Gi').set_memory_limit('32Gi').after(task1)#.set_accelerator_type("nvidia.com/gpu")
    
    task3 = prepare_bundle(config_file_path=config_file_path).set_caching_options(False).set_cpu_request('1000m').set_cpu_limit('8000m').set_memory_request('8Gi').set_memory_limit('32Gi').after(task2)#.set_accelerator_type("nvidia.com/gpu")

        
    

    # Use Dockerhub secrets to pull the image
    #kubernetes.set_image_pull_secrets(task1, secret_names=["maia-clou-ai-registry"])
    
    # Mount secret as volume for Kaniko credentials
    #kubernetes.use_secret_as_volume(task1, "maia-clou-ai-registry", "/kaniko/.docker")
        
    # Mount PVC to provide shared data
    kubernetes.mount_pvc(
        task1,
        pvc_name='shared',
        mount_path='/mnt/Data',
    )

    kubernetes.add_ephemeral_volume(task1, mount_path='/dev/shm', volume_name='shm', access_modes=['ReadWriteOnce'], size='2Gi',storage_class_name='local-path')

    kubernetes.mount_pvc(
        task2,
        pvc_name='shared',
        mount_path='/mnt/Data',
    )

    kubernetes.add_ephemeral_volume(task2, mount_path='/dev/shm', volume_name='shm', access_modes=['ReadWriteOnce'], size='2Gi',storage_class_name='local-path')

    kubernetes.mount_pvc(
        task3,
        pvc_name='shared',
        mount_path='/mnt/Data',
    )

    kubernetes.add_ephemeral_volume(task3, mount_path='/dev/shm', volume_name='shm', access_modes=['ReadWriteOnce'], size='2Gi',storage_class_name='local-path')

@dsl.pipeline(
    name="MONet Pipeline Training",
    description="Pipeline that runs the MONet Bundle Training."
)
def monet_pipeline_train(config_file_path: str):
    task1 = train(config_file_path=config_file_path).set_caching_options(False).set_cpu_request('1000m').set_cpu_limit('8000m').set_memory_request('8Gi').set_memory_limit('32Gi').set_accelerator_type("nvidia.com/gpu")
    kubernetes.mount_pvc(
            task1,
            pvc_name='shared',
            mount_path='/mnt/Data',
        )
        
    kubernetes.add_node_selector(task1, "kubernetes.io/hostname", "maia-small-5")
    kubernetes.add_ephemeral_volume(task1, mount_path='/dev/shm', volume_name='shm', access_modes=['ReadWriteOnce'], size='2Gi',storage_class_name='local-path')
    

@dsl.pipeline(
    name="MONet Pipeline Validation",
    description="Pipeline that runs the MONet Bundle Validation."
)
def monet_pipeline_validation(config_file_path: str):
    task1 = validate(config_file_path=config_file_path).set_caching_options(False).set_cpu_request('1000m').set_cpu_limit('8000m').set_memory_request('8Gi').set_memory_limit('32Gi').set_accelerator_type("nvidia.com/gpu")
    kubernetes.mount_pvc(
            task1,
            pvc_name='shared',
            mount_path='/mnt/Data',
        )
        
    kubernetes.add_node_selector(task1, "kubernetes.io/hostname", "maia-small-5")
    kubernetes.add_ephemeral_volume(task1, mount_path='/dev/shm', volume_name='shm', access_modes=['ReadWriteOnce'], size='2Gi',storage_class_name='local-path')


@dsl.pipeline(
    name="MONet Pipeline Convert CKPT to PT",
    description="Pipeline that runs the Conversion between the Lightning Checkpoint to PyTorch .pt format."
)
def monet_pipeline_convert_ckpt_to_pt(config_file_path: str):
    task1 = convert_ckpt_to_pt(config_file_path=config_file_path).set_caching_options(False).set_cpu_request('1000m').set_cpu_limit('8000m').set_memory_request('8Gi').set_memory_limit('32Gi').set_accelerator_type("nvidia.com/gpu")
    kubernetes.mount_pvc(
            task1,
            pvc_name='shared',
            mount_path='/mnt/Data',
        )
        
    kubernetes.add_node_selector(task1, "kubernetes.io/hostname", "maia-small-5")
    kubernetes.add_ephemeral_volume(task1, mount_path='/dev/shm', volume_name='shm', access_modes=['ReadWriteOnce'], size='2Gi',storage_class_name='local-path')

@dsl.pipeline(
    name="MONet Pipeline Convert PT to TS",
    description="Pipeline that runs the Conversion between the PyTorch .pt format to TensorFlow SavedModel format."
)
def monet_pipeline_convert_pt_to_ts(config_file_path: str):
    task1 = convert_ckpt_to_ts(config_file_path=config_file_path).set_caching_options(False).set_cpu_request('1000m').set_cpu_limit('8000m').set_memory_request('8Gi').set_memory_limit('32Gi').set_accelerator_type("nvidia.com/gpu")
    kubernetes.mount_pvc(
            task1,
            pvc_name='shared',
            mount_path='/mnt/Data',
        )
        
    kubernetes.add_node_selector(task1, "kubernetes.io/hostname", "maia-small-5")
    kubernetes.add_ephemeral_volume(task1, mount_path='/dev/shm', volume_name='shm', access_modes=['ReadWriteOnce'], size='2Gi',storage_class_name='local-path')


        


compiler.Compiler().compile(monet_pipeline_prepare_and_preprocess, package_path='MONet_pipeline_Plan_and_Preprocess.yaml')
compiler.Compiler().compile(monet_pipeline_train, package_path='MONet_pipeline_Train.yaml')
compiler.Compiler().compile(monet_pipeline_validation, package_path='MONet_pipeline_Validation.yaml')
compiler.Compiler().compile(monet_pipeline_convert_ckpt_to_pt, package_path='MONet_pipeline_Convert_CKPT_to_PT.yaml')
compiler.Compiler().compile(monet_pipeline_convert_ckpt_to_pt, package_path='MONet_pipeline_Convert_CKPT_to_PT.yaml')
compiler.Compiler().compile(monet_pipeline_convert_pt_to_ts, package_path='MONet_pipeline_Convert_PT_to_TS.yaml')