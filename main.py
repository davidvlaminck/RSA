from ReportLoopRunner import ReportLoopRunner

if __name__ == '__main__':
    reportlooprunner = ReportLoopRunner(settings_path=r'/home/davidlinux/Documents/AWV/resources/settings_RSA.json')
    # reportlooprunner = ReportLoopRunner(settings_path=r'C:\resources\settings_RSA.json')
    reportlooprunner.run()
