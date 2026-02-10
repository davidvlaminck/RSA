import sys
from pathlib import Path
import importlib

# Ensure project root is on sys.path so tests can import local modules like `lib` and `outputs`
PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pytest
from datetime import datetime, date
from unittest import mock

from lib.reports.DQReport import DQReport
from lib.mail.MailSender import MailSender


def test_empty_range():
    sender = MailSender(mail_settings={'host': 'localhost', 'username': 'u', 'password': 'p'})
    assert sender.mails_to_send == []
    report = DQReport(name='test report', title='test report title', spreadsheet_id='testsheetId')
    report.send_mails(sender=sender, named_range=[[]], previous_result=-1, result=-1)
    assert sender.mails_to_send == []


def test_wijziging_same_value_one_receiver():
    sender = MailSender(mail_settings={'host': 'localhost', 'username': 'u', 'password': 'p'})
    assert sender.mails_to_send == []
    report = DQReport(name='test report', title='test report title', spreadsheet_id='testsheetId')
    report.send_mails(sender=sender, named_range=[['david.vlaminck@mow.vlaanderen.be', 'Wijziging', '']], previous_result=0, result=0)
    assert sender.mails_to_send == []


def test_wijziging_different_values_one_receiver():
    sender = MailSender(mail_settings={'host': 'localhost', 'username': 'u', 'password': 'p'})
    assert sender.mails_to_send == []
    report = DQReport(name='test report', title='test report title', spreadsheet_id='testsheetId')
    report.send_mails(sender=sender, named_range=[['david.vlaminck@mow.vlaanderen.be', 'Wijziging', '']], previous_result=0, result=1)
    assert len(sender.mails_to_send) == 1
    assert sender.mails_to_send[0].receiver == 'david.vlaminck@mow.vlaanderen.be'
    assert sender.mails_to_send[0].report_name == 'test report title'
    assert sender.mails_to_send[0].count == 1


def test_wijziging_different_values_two_receivers():
    sender = MailSender(mail_settings={'host': 'localhost', 'username': 'u', 'password': 'p'})
    assert sender.mails_to_send == []
    report = DQReport(name='test report', title='test report title', spreadsheet_id='testsheetId')
    report.send_mails(sender=sender, named_range=[['david.vlaminck@mow.vlaanderen.be', 'Wijziging', ''],
                                                  ['second@mow.vlaanderen.be', 'Wijziging', '']],
                      previous_result=0, result=1)
    assert len(sender.mails_to_send) == 2
    assert sender.mails_to_send[0].receiver == 'david.vlaminck@mow.vlaanderen.be'
    assert sender.mails_to_send[1].receiver == 'second@mow.vlaanderen.be'


def test_daily_only_half_a_day_passed():
    # Patch the date used in the DQReport module to control today()
    dq_module = importlib.import_module('lib.reports.DQReport')
    with mock.patch.object(dq_module, 'date', wraps=datetime):
        # simulate today being 2022-01-01
        dq_module.date.today.return_value = date(2022, 1, 1)

        sender = MailSender(mail_settings={'host': 'localhost', 'username': 'u', 'password': 'p'})
        assert sender.mails_to_send == []
        report = DQReport(name='test report', title='test report title', spreadsheet_id='testsheetId')
        report.send_mails(sender=sender, named_range=[['david.vlaminck@mow.vlaanderen.be', 'Dagelijks', '2022-01-01 01:00:00']],
                          previous_result=0, result=1)
        assert sender.mails_to_send == []


def test_daily_one_day_passed():
    dq_module = importlib.import_module('lib.reports.DQReport')
    with mock.patch.object(dq_module, 'date', wraps=datetime):
        dq_module.date.today.return_value = date(2022, 1, 2)

        sender = MailSender(mail_settings={'host': 'localhost', 'username': 'u', 'password': 'p'})
        assert sender.mails_to_send == []
        report = DQReport(name='test report', title='test report title', spreadsheet_id='testsheetId')
        report.send_mails(sender=sender,
                          named_range=[['david.vlaminck@mow.vlaanderen.be', 'Dagelijks', '2022-01-01 01:00:00']],
                          previous_result=0, result=1)
        assert len(sender.mails_to_send) == 1
