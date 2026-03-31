from lib.reports.ReportLoopRunner import ReportLoopRunner
from scripts.ops.gdrive_upload import upload_folder_to_drive

if __name__ == '__main__':
    settings_path = r'/home/davidlinux/Documenten/AWV/resources/settings_RSA.json'
    onedrive_path = '/home/davidlinux/PycharmProjects/RSA/RSA_OneDrive'  # absoluut pad

    # Google Drive upload (optioneel) — zet DRIVE_UPLOAD = False om te disabelen
    DRIVE_UPLOAD = True
    DRIVE_TOKEN = '/home/davidlinux/Documenten/AWV/resources/gdrive_token.pkl'
    DRIVE_FOLDER = 'RSA_Reports'

    reportlooprunner = ReportLoopRunner(settings_path=settings_path, excel_output_dir=onedrive_path)

    if DRIVE_UPLOAD:
        reportlooprunner.on_run_complete = lambda: upload_folder_to_drive(
            local_folder=onedrive_path,
            drive_folder_name=DRIVE_FOLDER,
            token_path=DRIVE_TOKEN,
        )

    reportlooprunner.start(run_right_away=True)

# first on linux do: pip install psycopg2-binary

# bash script for VM
# #! usr/bin/bash
# # sleep 5h (possibly)
# export PYTHONPATH=/home/david/PycharmProjects/RSA:$PYTHONPATH
# ~/PycharmProjects/RSA/venv314/bin/python3.14 ~/PycharmProjects/RSA/main.py