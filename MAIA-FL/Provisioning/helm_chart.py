# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

import yaml
import shutil
from pathlib import Path
from nvflare.lighter.spec import Builder


class HelmChartBuilder(Builder):
    def __init__(self, docker_image, docker_registry_secret=None,storage_class=None,sftp_server_config=None):
        """Build Helm Chart."""
        self.docker_image = docker_image
        self.docker_registry_secret = docker_registry_secret
        self.storage_class = storage_class
        self.sftp_server_config = sftp_server_config

    def initialize(self, ctx):
        self.helm_chart_directory = os.path.join(self.get_wip_dir(ctx), "nvflare-chart")
        os.mkdir(self.helm_chart_directory)

    def _build_overseer(self, overseer, ctx):
        protocol = overseer.props.get("protocol", "http")
        default_port = "443" if protocol == "https" else "80"
        port = overseer.props.get("port", default_port)
        self.deployment_overseer["spec"]["template"]["spec"]["volumes"][0]["hostPath"][
            "path"
        ] = "{{ .Values.workspace }}"
        self.deployment_overseer["spec"]["template"]["spec"]["containers"][0]["ports"][0]["containerPort"] = port
        self.deployment_overseer["spec"]["template"]["spec"]["containers"][0]["image"] = self.docker_image
        self.deployment_overseer["spec"]["template"]["spec"]["containers"][0]["command"][
            0
        ] = f"/workspace/{overseer.name}/startup/start.sh"
        with open(os.path.join(self.helm_chart_templates_directory, "deployment_overseer.yaml"), "wt") as f:
            yaml.dump(self.deployment_overseer, f)

        self.service_overseer["spec"]["ports"][0]["port"] = port
        self.service_overseer["spec"]["ports"][0]["targetPort"] = port
        with open(os.path.join(self.helm_chart_templates_directory, "service_overseer.yaml"), "wt") as f:
            yaml.dump(self.service_overseer, f)

    def _build_server(self, server, ctx):
        server_name = server.name.replace(".","-")
        fed_learn_port = server.props.get("fed_learn_port", 30002)
        admin_port = server.props.get("admin_port", 30003)
        idx = ctx["index"]

        self.deployment_server["metadata"]["name"] = f"{server_name}"
        self.deployment_server["metadata"]["labels"]["system"] = f"{server_name}"

        self.deployment_server["spec"]["selector"]["matchLabels"]["system"] = f"{server_name}"

        self.deployment_server["spec"]["template"]["metadata"]["labels"]["system"] = f"{server_name}"
        #self.deployment_server["spec"]["template"]["spec"]["volumes"][0]["hostPath"]["path"] = "{{ .Values.workspace }}"
        #self.deployment_server["spec"]["template"]["spec"]["volumes"][1]["hostPath"]["path"] = "{{ .Values.persist }}"
        self.deployment_server["spec"]["template"]["spec"]["volumes"][0] = {}
        self.deployment_server["spec"]["template"]["spec"]["volumes"][1] = {}

        self.deployment_server["spec"]["template"]["spec"]["volumes"].append({})
        self.deployment_server["spec"]["template"]["spec"]["volumes"][2]["name"]="shm-volume"
        self.deployment_server["spec"]["template"]["spec"]["volumes"][2]["emptyDir"]={"medium":"Memory"}
        self.deployment_server["spec"]["template"]["spec"]["containers"][0]["volumeMounts"].append({"name":"shm-volume","mountPath":"/dev/shm"})

        self.deployment_server["spec"]["template"]["spec"]["volumes"][0]["persistentVolumeClaim"] = {}
        self.deployment_server["spec"]["template"]["spec"]["volumes"][0]["name"] = "workspace"
        self.deployment_server["spec"]["template"]["spec"]["volumes"][1]["persistentVolumeClaim"] = {}
        self.deployment_server["spec"]["template"]["spec"]["volumes"][1]["name"] = "persist"
        self.deployment_server["spec"]["template"]["spec"]["volumes"][0]["persistentVolumeClaim"]["claimName"] = "{{ .Values.workspace }}"
        self.deployment_server["spec"]["template"]["spec"]["volumes"][1]["persistentVolumeClaim"]["claimName"] = "{{ .Values.persist }}"
        self.deployment_server["spec"]["template"]["spec"]["containers"][0]["name"] = f"{server_name}"
        self.deployment_server["spec"]["template"]["spec"]["containers"][0]["image"] = self.docker_image
        self.deployment_server["spec"]["template"]["spec"]["containers"][0]["ports"][0][
            "containerPort"
        ] = fed_learn_port
        self.deployment_server["spec"]["template"]["spec"]["containers"][0]["ports"][1]["containerPort"] = admin_port
        cmd_args = self.deployment_server["spec"]["template"]["spec"]["containers"][0]["args"]
        for i, item in enumerate(cmd_args):
            if "/workspace/server" in item:
                cmd_args[i] = f"/workspace/{server.name}"
            if "__org_name__" in item:
                cmd_args[i] = f"org={server.org}"
        self.deployment_server["spec"]["template"]["spec"]["containers"][0]["args"] = cmd_args
        self.deployment_server["spec"]["template"]["spec"]["containers"][0]["resources"] = {
            "limits": {"nvidia.com/gpu": "1", "cpu": '8',
                       "memory": "64Gi"},
            "requests": {"nvidia.com/gpu": "1", "cpu": '8',
                         "memory": "64Gi"},
        }
        self.deployment_server["spec"]["template"]["spec"]["containers"][0]["command"][0] = "python"
        if self.docker_registry_secret is not None:
            self.deployment_server["spec"]["template"]["spec"]["imagePullSecrets"] = [{"name":self.docker_registry_secret}]
        
        
        with open(os.path.join(self.helm_chart_templates_directory, f"deployment_server_{server.name}.yaml"), "wt") as f:
            yaml.dump(self.deployment_server, f)
        
        self.pvc_workspace_server["spec"]["accessModes"] = []
        self.pvc_workspace_server["spec"]["accessModes"].append("ReadWriteOnce")
        self.pvc_workspace_server["metadata"]["name"] = "{{ .Values.workspace }}"
        self.pvc_workspace_server["spec"]["resources"] = {}
        self.pvc_workspace_server["spec"]["resources"]["requests"] = {}
        self.pvc_workspace_server["spec"]["resources"]["requests"]["storage"] = "1Gi"
        if self.storage_class is not None:
            self.pvc_workspace_server["spec"]["storageClassName"] = self.storage_class
        with open(os.path.join(self.helm_chart_templates_directory, f"pvc_workspace_server_{server.name}.yaml"), "wt") as f:
            yaml.dump(self.pvc_workspace_server, f)
        
        self.pvc_persistent_server["spec"]["accessModes"] = []
        self.pvc_persistent_server["spec"]["accessModes"].append("ReadWriteOnce")
        self.pvc_persistent_server["metadata"]["name"] = "{{ .Values.persist }}"
        self.pvc_persistent_server["spec"]["resources"] = {}
        self.pvc_persistent_server["spec"]["resources"]["requests"] = {}
        self.pvc_persistent_server["spec"]["resources"]["requests"]["storage"] = "1Gi"
        if self.storage_class is not None:
            self.pvc_persistent_server["spec"]["storageClassName"] = self.storage_class
        with open(os.path.join(self.helm_chart_templates_directory, f"pvc_persistent_server_{server.name}.yaml"), "wt") as f:
            yaml.dump(self.pvc_persistent_server, f)

        self.service_server["metadata"]["name"] = f"{server_name}"
        self.service_server["metadata"]["labels"]["system"] = f"{server_name}"

        self.service_server["spec"]["type"] = "NodePort"
        self.service_server["spec"]["selector"]["system"] = f"{server_name}"
        self.service_server["spec"]["ports"][0]["name"] = "fl-port"
        self.service_server["spec"]["ports"][0]["port"] = fed_learn_port
        self.service_server["spec"]["ports"][0]["targetPort"] = fed_learn_port
        self.service_server["spec"]["ports"][0]["nodePort"] = fed_learn_port
        self.service_server["spec"]["ports"][1]["name"] = "admin-port"
        self.service_server["spec"]["ports"][1]["port"] = admin_port
        self.service_server["spec"]["ports"][1]["targetPort"] = admin_port
        self.service_server["spec"]["ports"][1]["nodePort"] = admin_port

        with open(os.path.join(self.helm_chart_templates_directory, f"service_server_{server.name}.yaml"), "wt") as f:
            yaml.dump(self.service_server, f)

        if self.sftp_server_config:
            self.sftp_server_deployment["metadata"]["name"] = f"{server_name}-sftp"
            self.sftp_server_deployment["metadata"]["labels"] = {}
            self.sftp_server_deployment["metadata"]["labels"]["system"] = f"{server_name}-sftp"
            self.sftp_server_deployment["spec"]["selector"] = {}
            self.sftp_server_deployment["spec"]["selector"]["matchLabels"] = {}
            self.sftp_server_deployment["spec"]["selector"]["matchLabels"]["system"] = f"{server_name}-sftp"
            self.sftp_server_deployment["spec"]["template"] = {}
            self.sftp_server_deployment["spec"]["template"]["metadata"] = {}
            self.sftp_server_deployment["spec"]["template"]["metadata"]["labels"] = {}
            self.sftp_server_deployment["spec"]["template"]["metadata"]["labels"]["system"] = f"{server_name}-sftp"
            self.sftp_server_deployment["spec"]["template"]["spec"] = {}
            self.sftp_server_deployment["spec"]["template"]["spec"]["volumes"] = [{"name":"workspace-pv","persistentVolumeClaim":{"claimName":"{{ .Values.workspace }}"}}]
            self.sftp_server_deployment["spec"]["template"]["spec"]["containers"] = [{
            "name": f"{server_name}-sftp",
            "image": self.sftp_server_config["image"],
            "env":[ {"name":k,"value":v} for k,v in self.sftp_server_config["env"].items()
                #{"name":"n_users","value":"1"},
                #{"name":"user","value":"simone"},
                #"name":"email","value":"simben@kth.se"},
                #{"name":"password","value":"simben"},
                #{"name":"RUN_FILEBROWSER","value":"True"},
                #{"name":"RUN_VNC","value":"False"},
                #{"name":"HIVE_CONDA_ENABLED","value":"True"},
                #{"name":"RUN_MLFLOW_SERVER","value":"False"}
            ],
            "volumeMounts": [{"name":"workspace-pv","mountPath":self.sftp_server_config["mount_path"]}]
            }
            ]
            if self.docker_registry_secret is not None:
                self.sftp_server_deployment["spec"]["template"]["spec"]["imagePullSecrets"] = [{"name":self.docker_registry_secret}]

            with open(os.path.join(self.helm_chart_templates_directory, f"deployment_sftp_server_{server.name}.yaml"), "wt") as f:
                yaml.dump(self.sftp_server_deployment, f)

            self.sftp_server_service["metadata"]["name"] = f"{server_name}-sftp"
            self.sftp_server_service["metadata"]["labels"] = {}
            self.sftp_server_service["metadata"]["labels"]["system"] = f"{server_name}-sftp"
            self.sftp_server_service["spec"]["ports"] = [
            {
                "name":"file-browser",
                "protocol":"TCP",
                "port":80,
                "targetPort": 80
            },
                {
                "name":"ssh",
                "protocol":"TCP",
                "port":22,
                "targetPort": 22
            }
            ]
            self.sftp_server_service["spec"]["selector"] = {"system":f"{server_name}-sftp"}

            with open(os.path.join(self.helm_chart_templates_directory, f"service_sftp_server_{server.name}.yaml"), "wt") as f:
                yaml.dump(self.sftp_server_service, f)
            
    def _build_client(self, client, ctx):
        idx = ctx["index"]
        Path(os.path.join(self.helm_chart_templates_directory,f"{client.name}")).mkdir(parents=True,exist_ok=True)
        self.deployment_client["metadata"]["name"] = f"{client.name}"
        self.deployment_client["metadata"]["labels"]["system"] = f"{client.name}"

        self.deployment_client["spec"]["selector"]["matchLabels"]["system"] = f"{client.name}"

        self.deployment_client["spec"]["template"]["metadata"]["labels"]["system"] = f"{client.name}"
        #self.deployment_server["spec"]["template"]["spec"]["volumes"][0]["hostPath"]["path"] = "{{ .Values.workspace }}"
        #self.deployment_server["spec"]["template"]["spec"]["volumes"][1]["hostPath"]["path"] = "{{ .Values.persist }}"
        self.deployment_client["spec"]["template"]["spec"]["volumes"][0] = {}
        self.deployment_client["spec"]["template"]["spec"]["volumes"][1] = {}

        self.deployment_client["spec"]["template"]["spec"]["volumes"][2] = {}
        self.deployment_client["spec"]["template"]["spec"]["volumes"][2]["name"]="shm-volume"
        self.deployment_client["spec"]["template"]["spec"]["volumes"][2]["emptyDir"]={"medium":"Memory"}
        self.deployment_client["spec"]["template"]["spec"]["containers"][0]["volumeMounts"].append(
            {"name": "shm-volume", "mountPath": "/dev/shm"})

        self.deployment_client["spec"]["template"]["spec"]["volumes"][0]["persistentVolumeClaim"] = {}
        self.deployment_client["spec"]["template"]["spec"]["volumes"][0]["name"] = "workspace"
        self.deployment_client["spec"]["template"]["spec"]["volumes"][1]["persistentVolumeClaim"] = {}
        self.deployment_client["spec"]["template"]["spec"]["volumes"][1]["name"] = "persist"
        self.deployment_client["spec"]["template"]["spec"]["volumes"][0]["persistentVolumeClaim"]["claimName"] = "{{ .Values.workspace }}"
        self.deployment_client["spec"]["template"]["spec"]["volumes"][1]["persistentVolumeClaim"]["claimName"] = "{{ .Values.persist }}"
        self.deployment_client["spec"]["template"]["spec"]["containers"][0]["name"] = f"{client.name}"
        self.deployment_client["spec"]["template"]["spec"]["containers"][0]["image"] = self.docker_image
        
        
        args = ["-u", "-m", "nvflare.private.fed.app.client.client_train", "-m", f"/workspace/{client.name}",
                "-s", "fed_client.json", "--set", "secure_train=true", f"uid={client.name}", f"org={client.org}", "config_folder=config"]
        self.deployment_client["spec"]["template"]["spec"]["containers"][0]["args"] = args
        self.deployment_client["spec"]["template"]["spec"]["containers"][0]["resources"] = {
            "limits": {"nvidia.com/gpu": "1","cpu": '8',
              "memory": "64Gi"},
            "requests": {"nvidia.com/gpu": "1","cpu": '8',
              "memory": "64Gi"},
        }
        self.deployment_client["spec"]["template"]["spec"]["containers"][0]["command"][0] = "python"
        if self.docker_registry_secret is not None:
            self.deployment_client["spec"]["template"]["spec"]["imagePullSecrets"] = [{"name":self.docker_registry_secret}]
        
        with open(os.path.join(self.helm_chart_templates_directory,f"{client.name}", f"deployment_client_{client.name}.yaml"), "wt") as f:
            yaml.dump(self.deployment_client, f)
        
        self.pvc_workspace_client["spec"]["accessModes"] = []
        self.pvc_workspace_client["spec"]["accessModes"].append("ReadWriteOnce")
        self.pvc_workspace_client["metadata"]["name"] = "{{ .Values.workspace }}"
        self.pvc_workspace_client["spec"]["resources"] = {}
        self.pvc_workspace_client["spec"]["resources"]["requests"] = {}
        self.pvc_workspace_client["spec"]["resources"]["requests"]["storage"] = "1Gi"
        if self.storage_class is not None:
            self.pvc_workspace_client["spec"]["storageClassName"] = self.storage_class
        with open(os.path.join(self.helm_chart_templates_directory,f"{client.name}", f"pvc_workspace_client_{client.name}.yaml"), "wt") as f:
            yaml.dump(self.pvc_workspace_client, f)
        
        self.pvc_persistent_client["spec"]["accessModes"] = []
        self.pvc_persistent_client["spec"]["accessModes"].append("ReadWriteOnce")
        self.pvc_persistent_client["metadata"]["name"] = "{{ .Values.persist }}"
        self.pvc_persistent_client["spec"]["resources"] = {}
        self.pvc_persistent_client["spec"]["resources"]["requests"] = {}
        self.pvc_persistent_client["spec"]["resources"]["requests"]["storage"] = "1Gi"
        if self.storage_class is not None:
            self.pvc_persistent_client["spec"]["storageClassName"] = self.storage_class
        with open(os.path.join(self.helm_chart_templates_directory,f"{client.name}", f"pvc_persistent_client_{client.name}.yaml"), "wt") as f:
            yaml.dump(self.pvc_persistent_client, f)

        if self.sftp_server_config:
            self.sftp_server_deployment["metadata"]["name"] = f"{client.name}-sftp"
            self.sftp_server_deployment["metadata"]["labels"] = {}
            self.sftp_server_deployment["metadata"]["labels"]["system"] = f"{client.name}-sftp"
            self.sftp_server_deployment["spec"]["selector"] = {}
            self.sftp_server_deployment["spec"]["selector"]["matchLabels"] = {}
            self.sftp_server_deployment["spec"]["selector"]["matchLabels"]["system"] = f"{client.name}-sftp"
            self.sftp_server_deployment["spec"]["template"] = {}
            self.sftp_server_deployment["spec"]["template"]["metadata"] = {}
            self.sftp_server_deployment["spec"]["template"]["metadata"]["labels"] = {}
            self.sftp_server_deployment["spec"]["template"]["metadata"]["labels"]["system"] = f"{client.name}-sftp"
            self.sftp_server_deployment["spec"]["template"]["spec"] = {}
            self.sftp_server_deployment["spec"]["template"]["spec"]["volumes"] = [{"name":"workspace-pv","persistentVolumeClaim":{"claimName":"{{ .Values.workspace }}"}}]
            self.sftp_server_deployment["spec"]["template"]["spec"]["containers"] = [{
            "name": f"{client.name}-sftp",
            "image": self.sftp_server_config["image"],
             "env":[ {"name":k,"value":v} for k,v in self.sftp_server_config["env"].items()

            ],
            "volumeMounts":[{"name":"workspace-pv","mountPath":self.sftp_server_config["mount_path"]}]
            }
            ]
            self.sftp_server_deployment["spec"]["template"]["spec"]["imagePullSecrets"] = [{"name":"docker-registry-secret"}]

            with open(os.path.join(self.helm_chart_templates_directory,f"{client.name}", f"deployment_sftp_server_{client.name}.yaml"), "wt") as f:
                yaml.dump(self.sftp_server_deployment, f)

            self.sftp_server_service["metadata"]["name"] = f"{client.name}-sftp"
            self.sftp_server_service["metadata"]["labels"] = {}
            self.sftp_server_service["metadata"]["labels"]["system"] = f"{client.name}-sftp"
            self.sftp_server_service["spec"]["ports"] = [
            {
                "name":"file-browser",
                "protocol":"TCP",
                "port":80,
                "targetPort": 80
            },
                {
                "name":"ssh",
                "protocol":"TCP",
                "port":22,
                "targetPort": 22
            }
            ]
            self.sftp_server_service["spec"]["selector"] = {"system":f"{client.name}-sftp"}

            with open(os.path.join(self.helm_chart_templates_directory,f"{client.name}", f"service_sftp_server_{client.name}.yaml"), "wt") as f:
                yaml.dump(self.sftp_server_service, f)
        
    def build(self, project, ctx):
        self.template = ctx.get("template")

        with open(os.path.join(self.helm_chart_directory, "Chart.yaml"), "wt") as f:
            yaml.dump(yaml.safe_load(self.template.get("helm_chart_chart")), f)
        
        values = {}
        values["persist"] = "persist-pvc"
        values["workspace"] = "workspace-pvc"
        with open(os.path.join(self.helm_chart_directory, "values.yaml"), "wt") as f:
            yaml.dump(values, f)

        self.service_overseer = yaml.safe_load(self.template.get("helm_chart_service_overseer"))
        self.service_server = yaml.safe_load(self.template.get("helm_chart_service_server"))

        self.deployment_overseer = yaml.safe_load(self.template.get("helm_chart_deployment_overseer"))
        self.deployment_server = yaml.safe_load(self.template.get("helm_chart_deployment_server"))
        
        
        self.sftp_server_deployment = {}
        self.sftp_server_deployment["apiVersion"] = "apps/v1"
        self.sftp_server_deployment["kind"] = "Deployment"
        self.sftp_server_deployment["metadata"] = {}
        self.sftp_server_deployment["spec"] = {}
        
        self.sftp_server_service = {}
        self.sftp_server_service["apiVersion"] = "v1"
        self.sftp_server_service["kind"] = "Service"
        self.sftp_server_service["metadata"] = {}
        self.sftp_server_service["spec"] = {}
        
        self.pvc_workspace_server = {}
        self.pvc_workspace_server["apiVersion"] = "v1"
        self.pvc_workspace_server["kind"] = "PersistentVolumeClaim"
        self.pvc_workspace_server["metadata"] = {}
        self.pvc_workspace_server["spec"] = {}
        
        self.pvc_persistent_server = {}
        self.pvc_persistent_server["apiVersion"] = "v1"
        self.pvc_persistent_server["kind"] = "PersistentVolumeClaim"
        self.pvc_persistent_server["metadata"] = {}
        self.pvc_persistent_server["spec"] = {}
        
    
        self.helm_chart_templates_directory = os.path.join(self.helm_chart_directory, "templates")
        os.mkdir(self.helm_chart_templates_directory)
        overseer = project.get_participants_by_type("overseer")
        #self._build_overseer(overseer, ctx)
        self.deployment_client = self.deployment_server
        self.pvc_workspace_client = self.pvc_workspace_server
        self.pvc_persistent_client = self.pvc_persistent_server
        servers = project.get_participants_by_type("server", first_only=False)
        for index, server in enumerate(servers):
            ctx["index"] = index
            self._build_server(server, ctx)
        clients = project.get_participants_by_type("client", first_only=False)
        for index, client in enumerate(clients):
            ctx["index"] = index
            self._build_client(client, ctx)