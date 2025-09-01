# MAIA-AIDA-TechDays-Workshop
Repository containing presentation slides and supporting materials for MAIA Tutorial, AIDA Technical Days, 17 September.

## Table of Contents
- [MAIA-AIDA-TechDays-Workshop](#maia-aida-techdays-workshop)
  - [Table of Contents](#table-of-contents)
  - [Introduction to MAIA](#introduction-to-maia)
    - [MAIA in 5 minutes](#maia-in-5-minutes)
      - [MAIA Projects](#maia-projects)
    - [User Registration](#user-registration)
    - [MAIA Dashboard Overview](#maia-dashboard-overview)
      - [MAIA Project Page](#maia-project-page)
    - [Connect VSCode to your running MAIA Workspace](#connect-vscode-to-your-running-maia-workspace)
  - [Part 1: End-to-End Model Development and Deployment Workflow](#part-1-end-to-end-model-development-and-deployment-workflow)
    - [Overview](#overview)
    - [Prerequisites](#prerequisites)
    - [1. DICOM Transfer to Orthanc](#1-dicom-transfer-to-orthanc)
    - [1.1 DICOM Manual Annotation \[Optional\]](#11-dicom-manual-annotation-optional)


## Introduction to MAIA
### MAIA in 5 minutes

MAIA is a collaborative platform designed to manage Medical AI research efficiently and at scale. It brings together state-of-the-art, standards-based tools to cover every stage of the AI lifecycle in the medical domain, from data management and annotation to model training, deployment, and evaluation. Multiple projects can be independently hosted within MAIA, and each user can participate in one or more projects. Built as a federation of clusters, MAIA allows physically independent computing infrastructures to be unified under one platform, abstracting away the complexity so researchers can focus on collaboration and innovation without worrying about the underlying systems.

<p align="center">
    <img src="./img/MAIA_Clusters.png" alt="MAIA Clusters Overview" style="width:50%;" />
</p>

#### MAIA Projects  

Each **MAIA Project** is provisioned with a dedicated *MAIA Namespace*, which serves as a container for all the applications required to develop, deploy, and curate medical images along with their corresponding AI models.  

- **Medical Images**: Managed through *Orthanc*, which acts as the project’s DICOM server and entry point for storing and accessing imaging data.  
- **Model Development & Scientific Computing**: Provided via the *MAIA Workspace* inside the namespace, giving users isolated or shared environments.  

Entrypoints to the workspace include:  
- Remote Desktop  
- Jupyter Interface  
- SSH Connection  

<p align="center">
  <img src="https://raw.githubusercontent.com/kthcloud/maia/master/dashboard/image/README/MAIA_Workspace.png" width="90%" alt='MAIA'>
</p>

### User Registration
To register in the MAIA Project, created for the MAIA Workshop, and getting access to the resources, please follow these steps:

1. Visit the [MAIA Project Registration Page](https://maia.app.cloud.cbh.kth.se/maia/register/).
2. Fill out the registration form with the required information. Under "Existing Project", select "aida-workshop".
3. Submit the form and check your email for a confirmation message.
4. Follow the instructions in the email to complete your registration.

Once registered, you will have access to all workshop materials and resources.
<p align="center">
    <img src="./img/Registration_Form.png" alt="Registration Form" style="width:50%;" />
</p>

### MAIA Dashboard Overview
After logging in, you will be directed to the MAIA Dashboard. Here, you can have an overview of the MAIA Cluster resources, including information about the status of each cluster and node.

On the side, there is a navigation bar that allows you to access the different project pages you are assigned to.
By clicking on a project name, you can switch between different projects and access their specific resources and tools.

#### MAIA Project Page
The MAIA Project page is structured in four main sections:

1. **MAIA Apps**: A collection of applications and tools available for use within the project.
<p align="center">
    <img src="./img/MAIA-Apps.png" alt="MAIA Apps" style="width:50%;" />
</p>

2. **Remote Desktops**: This section provides a table listing each project user, along with a direct link to their Remote Desktop interface for accessing the MAIA Workspace. It also includes the corresponding SSH command for connecting to the MAIA Workspace.
<p align="center">
    <img src="./img/Desktops.png" alt="Remote Desktops" style="width:80%;" />
</p>

3. **MONAI Label Models**: A list of available models, deployed for integration in inference pipelines (MAIA Segmentation Portal, PACS Integration through XNAT or Orthanc), and Active Learning
<p align="center">
    <img src="./img/Models.png" alt="MONAI Label Models" style="width:60%;" />
</p>

4. **Orthanc DICOM Web**: A list of available Orthanc instances for the project, including a reference to the DICOMWeb and the DICOM C-GET and C-STORE endpoints.
<p align="center">
    <img src="./img/Orthanc.png" alt="Orthanc DICOM Web" style="width:70%;" />
</p>


### Connect VSCode to your running MAIA Workspace

You can connect VSCode (or any other IDE through SSH), by following these steps:

1. Upload a new or an existing SSH key following the instructions on the [MAIA Welcome](https://github.com/kthcloud/MAIA/blob/master/docker/MAIA-Workspace/Welcome.ipynb) page in your MAIA Workspace (`/home/maia-user/Welcome.ipynb`), either from the Jupyter interface or the Remote Desktop
2. Retrieve the SSH command to execute either from the same [MAIA Welcome](https://github.com/kthcloud/MAIA/blob/master/docker/MAIA-Workspace/Welcome.ipynb) page or from the MAIA Dashboard, under the **Remote Desktops** table.

## Part 1: End-to-End Model Development and Deployment Workflow
### Overview
This section outlines a complete, day-by-day workflow for developing, training, and deploying a medical imaging AI model.  
The process begins with DICOM data transfer and manual annotation, continues through dataset conversion, preprocessing, and model training, and concludes with packaging, deployment, and inference on both NIfTI and DICOM inputs.  
By the end of this sequence, you will have built and deployed a model that is fully integrated into a clinical-style pipeline.


### Prerequisites
You will need a DICOM dataset to upload into MAIA.  

- To download a sample dataset, visit the [Decathlon Challenge](http://medicaldecathlon.com/) website or follow the instructions in [Kubeflow - Download Dataset from Decathlon Challenge](./Kubeflow.ipynb#Download-Spleen-Decathlon-Dataset).  
- Since the dataset is provided in NIfTI format, you will need to convert it to DICOM. Follow the steps in [Kubeflow - Convert NIfTI to DICOM](./Kubeflow.ipynb#Convert-NIFTI-to-DICOM).  

For convenience, an example DICOM dataset with 5 abdominal CT scans (converted from the Task09-Spleen Decathlon dataset) is available here:  
[MinIO - DICOM Spleen Dataset]()

### 1. DICOM Transfer to Orthanc  

The first step in the AI lifecycle is transferring the DICOM dataset to a MAIA project, making it accessible for subsequent processing and model training. In MAIA, *Orthanc* serves as the entry point for sharing DICOM files within a project.  

Orthanc supports three methods for transferring DICOM files:  
- **DICOMWeb**  
- **DICOM C-STORE**  
- **Orthanc Web Interface**  

For DICOMWeb and C-STORE, you can find the relevant links (for DICOMWeb) and commands (for C-STORE) in the MAIA Dashboard under the **Orthanc DICOM Web** table.  

When using C-STORE, ensure your calling AE title follows the pattern specified in the Orthanc link, e.g., `aida-workshop.maia.se/orthanc-<your-ae-title>`. Alternatively, the AE Title can also be found in the **Modalities** section of the Orthanc Web interface.  

As a third option, files can be uploaded directly via drag-and-drop using the Orthanc Web UI.

Once uploaded, the DICOM files can be accessed, inspected, and visualized through the Orthanc instance along with its integrated OHIF viewer.

### 1.1 DICOM Manual Annotation [Optional]  

For supervised tasks, both the medical images and their corresponding annotated masks are required for the model to learn the desired task. Existing segmentation masks can be uploaded as DICOM SEG files using the same procedure as for the images through Orthanc. Alternatively, masks can be manually annotated using any of the tools available in MAIA:  

- **OHIF Viewer Annotation Tools**  
- **3D Slicer in the MAIA Workspace**: Link 3D Slicer to Orthanc as a DICOM server, download the images into Slicer, and upload the annotated masks. Upload can be done using either DICOMWeb or DICOM C-STORE protocols.  

The main advantage of using tools like 3D Slicer in the MAIA Workspace or the OHIF interface is that both the workspace and Orthanc are within the same internal network. This allows communication with Orthanc via its internal IP, e.g., `aida-workshop-orthanc-svc-orthanc:4242`, ensuring that the data never leave the platform and remain fully secure.

