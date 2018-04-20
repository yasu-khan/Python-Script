#!/usr/bin/python

"""
    Author      :   Yasser Khan
    Date        :   21-JUNE-2017
    Description :   This program is for generating consolidated FSFO Failover and Reinstate report for specified/provided window time frame.

    Modification
    Date          Author          Comments
    ------------  --------------  ---------------------------------------------------------------------------------------------------------------
    04-JUNE-2017  YAK             Incorporate gen_report_data, gen_report_html and send_mail function for reporting purpose.
"""

import sys
import os
import glob
import collections
import textwrap
from datetime import datetime


def formatted_datetime(date_str):
    """
    Return date in format defined as per Observer log file.
    """

    return datetime.strptime(date_str, '%H:%M:%S.%f  %A, %B %d, %Y')


def sub_dates(date1, date2):
    """
    Subtract two dates and return the difference
    """

    start = formatted_datetime(date1)
    end = formatted_datetime(date2)
    delta = end - start

    return delta


def check_arguments():
    """
    Argument handling of the script
    """

    if len(sys.argv) < 2 or len(sys.argv) > 2:
        print "Invlid arguments passed to this script. Please pass just one argument which defines frquency of reporting in days"
        sys.exit()
    else:
        reporting_days = int(sys.argv[1])

    return reporting_days


def gen_html_report(start_date, end_date, failover_lists=None, reinstate_lists=None):
    total_fail = 0 
    total_reinstate = 0 
    max_time_fail = 0 
    min_time_fail = 0 
    max_time_reinstate = 0 
    min_time_reinstate = 0
    html_failover_table = " "
    html_reinstate_table = " "

    if failover_lists is not None:
        total_fail = len(failover_lists)
        max_time_fail = (max(map(lambda x: x[-1] if "Failed" not in x else -99, failover_lists)))
        min_time_fail = (min(map(lambda x: x[-1] if "Failed" not in x else float("inf"), failover_lists)))

        html_records = "<tr>"
        for i in failover_lists:
            print failover_lists
            html_records += "<td>" + str(i[0]) + "</td>" + \
                            "<td>" + str(i[3]) + "</td>" + \
                            "<td>" + str(i[1]) + "</td>" + \
                            "<td>" + str(i[2]) + "</td>" + \
                            "<td>" + str(i[4]) + "</td></tr>" + "\n"

        html_failover_table = textwrap.dedent("""\
            <p style="text-align:left"><span style="font-size:16px"><span style="font-family:Arial,Helvetica,sans-serif"><strong>Detail report of FSFO Failover</strong></span></span></p>
            <table class="GeneratedTable" style="width: 60%;">
              <thead>
                <tr>
                  <th>Failover to DB</th>
                  <th>Status</th>
                  <th>Start Time</th>
                  <th>End Time</th>
                  <th>Total time taken</th>
                </tr>
              </thead>
                <tbody>
                  {0}
                </tbody>
            </table>
            """.format(html_records))

    if reinstate_lists is not None:
        print reinstate_lists
        total_reinstate = len(reinstate_lists)
        max_time_reinstate = (max(map(lambda x: x[-1] if "Failed" not in x else -99, reinstate_lists)))
        min_time_reinstate = (min(map(lambda x: x[-1] if "Failed" not in x else float("inf"), reinstate_lists)))

        html_records = "<tr>"
        for i in reinstate_lists:
            html_records += "<td>" + str(i[0]) + "</td>" + \
                            "<td>" + str(i[3]) + "</td>" + \
                            "<td>" + str(i[1]) + "</td>" + \
                            "<td>" + str(i[2]) + "</td>" + \
                            "<td>" + str(i[4]) + "</td></tr>" + "\n"

        html_reinstate_table = textwrap.dedent("""\
            <p style="text-align:left"><span style="font-size:16px"><span style="font-family:Arial,Helvetica,sans-serif"><strong>Detail report of FSFO Reinstate</strong></span></span></p>
            <table class="GeneratedTable" style="width: 60%;">
              <thead>
                <tr>
                  <th>Reinstate of DB</th>
                  <th>Status</th>
                  <th>Start Time</th>
                  <th>End Time</th>
                  <th>Total time taken</th>
                </tr>
              </thead>
                <tbody>
                  {0}
                </tbody>
            </table>
            """.format(html_records))

    summary_table = textwrap.dedent("""\
        <p style="text-align:left"><span style="font-size:16px"><span style="font-family:Arial,Helvetica,sans-serif"><strong>Summary report of FSFO</strong></span></span></p>
        <table class="GeneratedTable" style="width: 23%;">
          <thead>
            <tr>
              <th colspan="2">SUMMARY</th>
            </tr>
          </thead>
            <tbody>
              <tr>
                <td>Total databases failedover</td>
                <td>{0}</td>
              </tr><tr>
                <td>Total databases reinstated</td>
                <td>{1}</td>
              </tr><tr>
                <td>Maximum time for failover</td>
                <td>{2}</td>
              </tr><tr>
                <td>Minimum time for failover</td>
                <td>{3}</td>
              </tr><tr>
                <td>Maximum time for reinstate</td>
                <td>{4}</td>
              </tr><tr>
                <td>Minimum time for reinstate</td>
                <td>{5}</td>
              </tr>
            </tbody>
        </table>
        """.format(total_fail, total_reinstate, max_time_fail, min_time_fail, max_time_reinstate, min_time_reinstate))

    import subprocess
    p = subprocess.Popen("/bin/showlayout -h `hostname`", stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    location = output.splitlines()[4].split()[7]
    environ = output.splitlines()[4].split()[2]

    if location == "blocke":
        region = "Eagan"
    elif location == "plano":
        region = "Plano"
    elif location == "dtc":
        region = "Dockland"
    elif location == "hzl":
        region = "Hazelwood"
    elif location == "uk1":
        region = "UK1"
    elif location == "sgp":
        region = "Singapore"

    if environ != "prod":
        env = "QA/Client"
    else:
        env = "Prod"

    html_code = textwrap.dedent("""\
        <p style="text-align:center"><span style="font-size:23px"><span style="font-family:Arial,Helvetica,sans-serif"><strong>FSFO Report - Failover and Reinstate ({0} Region {1})</strong></span></span></p>
        <p style="text-align:center"><span style="font-size:23px"><span style="font-family:Arial,Helvetica,sans-serif"><strong>({2} to {3})</strong></span></span></p>

        <style>
        table.GeneratedTable {{
          background-color: #ffffff;
          border-collapse: collapse;
          border-width: 2px;
          border-color: #000000;
          border-style: solid;
          color: #000000;
          text-align: center
        }}

        table.GeneratedTable td, table.GeneratedTable th {{
          border-width: 2px;
          border-color: #000000;
          border-style: solid;
          padding: 3px;
        }}

        table.GeneratedTable thead {{
          background-color: #ff8000;
        }}
        </style>
        {4}
        <br></br>
        {5}
        <br></br>
        {6}
        """.format(env, region, start_date, end_date, summary_table, html_failover_table, html_reinstate_table))

    return html_code, env, region


def send_mail(html_content, environment, region):
    import smtplib

    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    me = "SERVER@example.com"
    you = "CLIENT@example.com"

    msg = MIMEMultipart('alternative')
    msg['Subject'] = "FSFO Report - Failover/Reinstate " + "(" + environment + " Region " + region + ")"
    msg['From'] = me
    msg['To'] = you

    html = html_content
    part = MIMEText(html, 'html')
    msg.attach(part)

    s = smtplib.SMTP('relay-service')
    s.sendmail(me, you, msg.as_string())
    s.quit()

    return


def gen_report_data(days=7):
    """
    This function will send consolidated FSFO Failover and Reinstate report after defined window time
    """

    track_report_file = "/tmp/.master_track_report_file"
    delta_file = "/tmp/master_delta.info"
    window_frame = int(days)

    if not os.path.exists(track_report_file):
        seek_from = 0
        old_report_dt = datetime.now().strftime('%H:%M:%S.%f  %A, %B %d, %Y')
        with open(track_report_file, 'w') as trfile:
            trfile.write(str(seek_from) + " - " + old_report_dt)
    else:
        with open(track_report_file, 'r') as trfile:
            seek_from, old_report_dt = map(lambda s: s.strip(), trfile.readline().split('-'))

    current_report_dt = datetime.now().strftime('%H:%M:%S.%f  %A, %B %d, %Y')
    report_days_old = sub_dates(old_report_dt, current_report_dt)

    if int(report_days_old.days) >= window_frame:
        with open(track_report_file, 'w') as trfile:
            with open(delta_file, 'r') as deltafd:
                deltafd.seek(int(seek_from), 0)
                fail_det = []
                reins_det = []
                for line in deltafd:
                    if line and not line.startswith('\n'):
                        record = line.split('-')
                        if "Failover" in record[0] and "Failed" not in record[3]:
                            tot_time = (sum(int(x) * 60 ** i for i, x in enumerate(
                                reversed(record[3].split('=>')[1].strip().split(".")[0].split(":")))))
                            fail_det.append([record[0].split('=>')[1].strip(), record[1].split('=>')[1].strip(),
                                             record[2].split('=>')[1].strip(), "Success", tot_time])
                        elif "Failover" in record[0] and "Failed" in record[3]:
                            tot_time = (sum(int(x) * 60 ** i for i, x in enumerate(
                                reversed(record[3].split('=>')[1].strip().split(".")[0].split(":")))))
                            fail_det.append([record[0].split('=>')[1].strip(), record[1].split('=>')[1].strip(),
                                             record[2].split('=>')[1].strip(), "Failed", tot_time])
                        elif "Reinstate" in record[0] and len(record) < 4:
                            reins_det.append([record[0].split('=>')[1].strip(), record[1].split('=>')[1].strip(), 
                                             "no_value", "Failed", "no_value"])
                        elif "Reinstate" in record[0] and "failed" not in record[2]:
                            tot_time = (sum(int(x) * 60 ** i for i, x in enumerate(
                                reversed(record[3].split('=>')[1].strip().split(".")[0].split(":")))))
                            reins_det.append([record[0].split('=>')[1].strip(), record[1].split('=>')[1].strip(),
                                              record[2].split('=>')[1].strip(), "Success", tot_time])
                        elif "Reinstate" in record[0] and "failed" in record[2]:
                            tot_time = (sum(int(x) * 60 ** i for i, x in enumerate(
                                reversed(record[3].split('=>')[1].strip().split(".")[0].split(":")))))
                            reins_det.append([record[0].split('=>')[1].strip(), record[1].split('=>')[1].strip(),
                                              record[2].split('=>')[1].strip(), "Failed", tot_time])
                read_end_pos = deltafd.tell()
                trfile.write(str(read_end_pos) + " - " + current_report_dt)

                display_old_report_dt = datetime.strptime(old_report_dt, '%H:%M:%S.%f  %A, %B %d, %Y')
                display_current_report_dt = datetime.strptime(current_report_dt, '%H:%M:%S.%f  %A, %B %d, %Y')
                start_date = display_old_report_dt.strftime("%Y-%B-%d")
                end_date = display_current_report_dt.strftime("%Y-%B-%d")
                if len(fail_det) > 0 and len(reins_det) > 0:
                    print "TRUE for both lists"
                    html_content = gen_html_report(start_date, end_date, fail_det, reins_det)
                    send_mail(html_content[0], html_content[1], html_content[2])
                elif len(fail_det) > 0:
                    print "TRUE for only fail_det lists"
                    html_content = gen_html_report(start_date, end_date, fail_det, None)
                    send_mail(html_content[0], html_content[1], html_content[2])
                elif len(reins_det) > 0:
                    print "TRUE for only reins_det lists"
                    html_content = gen_html_report(start_date, end_date, None, reins_det)
                    send_mail(html_content[0], html_content[1], html_content[2])

    return


def parse_observer_logs():
    """
    This function parse all the Observer log files to find Failover or Reinstate operation performed from the last processed point in time
    """

    tracking_file = "/tmp/.master_tracking_file"
    delta_file = "/tmp/master_delta.info"
    tarry = {}

    if not os.path.exists(tracking_file):
        seek_from = 0
    else:  # populate dictionary with seek details for each logfile
        with open(tracking_file, 'r') as tfile:
            for line in tfile:
                tarry[line.strip().split(',')[2]] = [line.split(',')[0], line.split(',')[1]]

    with open(tracking_file, 'w') as tracking_file_handle:
        with open(delta_file, 'a') as delta_file_fd:
            for log_file in glob.glob("/fsfo_log/*_observer.log"):
                obs_file_meta = os.stat(log_file)
                current_obs_file_inode = obs_file_meta.st_ino

                if log_file in tarry:
                    seek_file_inode = int(tarry[log_file][1])
                    if current_obs_file_inode != seek_file_inode:  # reset reading from begin if file has been archived
                        seek_from = 0
                    else:
                        seek_from = int(tarry[log_file][0])
                else:
                    seek_from = 0  # reset reading from begin for new log file

                with open(log_file) as f:
                    f.seek(seek_from, 0)
                    before = collections.deque(maxlen=1)
                    for line in f:
                        if line.startswith("Initiating Fast-Start"):
                            failover_to_db = line.split('"')[1]
                            failover_start_date = before[0]
                            delta_info = "\n" + "Failover to DB => " + failover_to_db + " - Start date ==> " + failover_start_date.strip()
                            delta_file_fd.write(delta_info)
                        if line.startswith("Failover succeeded"):
                            failover_end_date = next(f, 'Exhausted').strip()
                            failover_total_time = sub_dates(failover_start_date.strip(), failover_end_date.strip())
                            delta_info = " - End date ==> " + failover_end_date + " - Total time taken => " + str(failover_total_time)
                            delta_file_fd.write(delta_info)
                        if line.endswith("Failover failed. Quit observer.\n"):
                            failed_failover_date = before[0]
                            failed_failover_total_time = sub_dates(failover_start_date.strip(), failed_failover_date.strip())
                            delta_info = " - Failed at ==> " + failed_failover_date.strip() + " - Failed after total => " + str(failed_failover_total_time)
                            delta_file_fd.write(delta_info)
                        if line.startswith("Initiating reinstatement"):
                            reinstate_of_db = line.split('"')[1]
                            reinstate_start_date = before[0]
                            delta_info = "\n" + "Reinstate of DB => " + reinstate_of_db + " - Start date ==> " + reinstate_start_date.strip()
                            delta_file_fd.write(delta_info)
                        if line.startswith("Reinstatement of database"):
                            reinstate_status = line.strip().split()[4]
                            reinstate_end_date = next(f, 'Exhausted').strip()
                            reinstate_total_time = sub_dates(reinstate_start_date.strip(), reinstate_end_date.strip())
                            delta_info = " - " + reinstate_status + " End date ==> " + reinstate_end_date + " - Total time taken => " + str(reinstate_total_time)
                            delta_file_fd.write(delta_info)
                        before.append(line)
                    read_end_pos = f.tell()  # Get the end of read position
                    tracking_info = str(read_end_pos) + "," + str(current_obs_file_inode) + "," + str(log_file) + "\n"
                    tracking_file_handle.write(tracking_info)

    return


def main():
    reporting_days = check_arguments()
    parse_observer_logs()
    gen_report_data(reporting_days)


if __name__ == "__main__":
    main()

