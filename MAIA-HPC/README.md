# MAIA-HPC

This repository provides configuration templates and instructions for running **MAIA-HPC** experiments on your project.  

To get started, follow the setup guide in the official repository:  
👉 [MAIA-HPC Setup Instructions](https://github.com/kthcloud/MAIA/tree/master/MAIA-HPC)

---

## Server Configuration

First, configure the server by running:

```bash
configure_MAIA-HPC.sh
```

This will create the file `ssh_server.json`. It should look like the following example:

```json
{
    "project_id": "<your_project_id>",
    "partition": "gpu",
    "error_file": "logs/slurm-",
    "output_file": "logs/slurm-",
    "amd_gpu": true, // or "nvidia_gpu": true if using NVIDIA
    "project_dir": "<your_remote_project_directory>"
}
```

---

## Experiment Configuration

To set up an experiment, create a configuration file in the `experiments` folder.  

You can either:
- Use the interactive script:
  ```bash
  configure_experiment.sh
  ```
- Or import an existing configuration, for example the [**nnUNet Spleen training experiment**](./train_nnUNet_Spleen.json):
  ```bash
  import_experiment.sh train_nnUNet_Spleen.json
  ```

---

## SSH Configuration

Finally, add an entry to your `$HOME/ssh_config.ini` file. Example:

```ini
[<SERVER-NAME>-nnUNet-Spleen]
EXPERIMENT_NAME=train_nnUNet_Spleen
REMOTE_PATH=<your_remote_experiment_directory>
LOCAL_PATH=<your_local_experiment_directory>
```

Where:
- `<SERVER-NAME>` matches the name of your server in `ssh_server.json`
- `REMOTE_PATH` is the remote directory for the experiment
- `LOCAL_PATH` is the local directory where results will be synced

---

✅ With this setup, you are ready to run experiments on **MAIA-HPC**.