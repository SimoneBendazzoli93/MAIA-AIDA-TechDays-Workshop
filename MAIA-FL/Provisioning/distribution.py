import os
import shutil
import subprocess

from nvflare.lighter.spec import Builder, Project
from nvflare.lighter.utils import generate_password

class DistributionBuilder(Builder):
    def __init__(self, zip_password=False):
        """Build the zip files for each folder.
        Creates the zip files containing the archives for each startup kit. It will add password protection if the
        argument (zip_password) is true.
        Args:
            zip_password: if true, will create zipped packages with passwords
        """
        self.zip_password = zip_password

    def build(self, project: Project, ctx: dict):
        """Create a zip for each individual folder.
        Note that if zip_password is True, the zip command will be used to encrypt zip files.  Users have to
        install this zip utility before provisioning.  In Ubuntu system, use this command to install zip utility:
        sudo apt-get install zip
        Args:
            project (Project): project instance
            ctx (dict): the provision context
        """
        wip_dir = self.get_wip_dir(ctx)
        dirs = [
            name
            for name in os.listdir(wip_dir)
            if os.path.isdir(os.path.join(wip_dir, name))
        ]
        for dir in dirs:
            dest_zip_file = os.path.join(wip_dir, f"{dir}")
            if self.zip_password:
                pw = generate_password()
                print(dest_zip_file)
                run_args = ["zip", "-rq", "-P", pw, dest_zip_file + ".zip", ".", "-i", "*"]
                os.chdir(dest_zip_file)
                try:
                    subprocess.run(run_args)
                    print(f"Password {pw} on {dir}.zip")
                except FileNotFoundError:
                    raise RuntimeError("Unable to zip folders with password.  Maybe the zip utility is not installed.")
                finally:
                    os.chdir(os.path.join(dest_zip_file, ".."))
            else:
                shutil.make_archive(dest_zip_file, "zip", root_dir=os.path.join(wip_dir, dir))