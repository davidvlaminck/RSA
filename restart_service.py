import os
import subprocess
import time

if __name__ == '__main__':
    password = 'pwd'

    while True:
        command = 'sudo -S systemctl status neo4j'
        try:
            output = subprocess.check_output('echo %s | %s' % (password, command), shell=True)
            output_lines = output.decode('utf-8').split('\n')

            line_active = [line for line in output_lines if 'Active:' in line][0]
            line_active = line_active.split('Active:', 1)[1].strip()
            if line_active.startswith('active'):
                print('still active')
                time.sleep(300)
            else:
                print('not active')
                command = 'sudo -S systemctl start neo4j'
                os.system('echo %s | %s' % (password, command))
        except:
            print('probably not active')
            command = 'sudo -S systemctl start neo4j'
            os.system('echo %s | %s' % (password, command))
