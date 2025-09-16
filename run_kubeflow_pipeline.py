import os
import kfp
import click
import json

@click.command()
@click.option('--namespace',  help='Kubernetes namespace where the pipeline will be run.')
@click.option('--pipeline_name', help='Name of the pipeline to run.')
@click.option('--args', help='Path to the arguments file.')
def main(namespace, pipeline_name, args):
    os.environ["KF_PIPELINES_SA_TOKEN_PATH"] = "/var/run/secrets/kubeflow/pipelines/token"
    kfp_client = kfp.Client()

    with open(args, 'r') as file:
        arguments = json.load(file)

    kfp_client.create_run_from_pipeline_package( f"KubeFlow/Pipelines/{pipeline_name}.yaml", namespace=namespace,
                                                arguments=arguments
                                            )

if __name__ == "__main__":
    main()
