from lib.reports.ReportLoopRunner import ReportLoopRunner

if __name__ == '__main__':
    settings_path = r'/home/davidlinux/Documenten/AWV/resources/settings_RSA.json'
    onedrive_path = '/home/davidlinux/PycharmProjects/RSA/RSA_OneDrive'  # absoluut pad
    reportlooprunner = ReportLoopRunner(settings_path=settings_path, excel_output_dir=onedrive_path)
    # reportlooprunner = ReportLoopRunner(settings_path=r'C:\resources\settings_RSA.json')
    reportlooprunner.start(run_right_away=True)

# first on linux do: pip install psycopg2-binary

# bash script for VM
# #! usr/bin/bash
# # sleep 5h (possibly)
# export PYTHONPATH=/home/david/PycharmProjects/RSA:$PYTHONPATH
# ~/PycharmProjects/RSA/venv314/bin/python3.14 ~/PycharmProjects/RSA/main.py