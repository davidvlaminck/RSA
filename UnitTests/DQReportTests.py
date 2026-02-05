import unittest
from datetime import datetime, date
from unittest import mock

from lib.reports.DQReport import DQReport
from lib.mail.MailSender import MailSender


class DQReportTests(unittest.TestCase):
    def test_empty_range(self):
        sender = MailSender()
        self.assertListEqual([], sender.mails_to_send)
        report = DQReport(name='test report', title='test report title', spreadsheet_id='testsheetId')
        report.send_mails(sender=sender, named_range=[[]], previous_result=-1, result=-1)
        self.assertListEqual([], sender.mails_to_send)

    def test_wijziging_same_value_one_receiver(self):
        sender = MailSender()
        self.assertListEqual([], sender.mails_to_send)
        report = DQReport(name='test report', title='test report title', spreadsheet_id='testsheetId')
        report.send_mails(sender=sender, named_range=[['david.vlaminck@mow.vlaanderen.be', 'Wijziging', '']], previous_result=0, result=0)
        self.assertListEqual([], sender.mails_to_send)

    def test_wijziging_different_values_one_receiver(self):
        sender = MailSender()
        self.assertListEqual([], sender.mails_to_send)
        report = DQReport(name='test report', title='test report title', spreadsheet_id='testsheetId')
        report.send_mails(sender=sender, named_range=[['david.vlaminck@mow.vlaanderen.be', 'Wijziging', '']], previous_result=0, result=1)
        self.assertEqual(1, len(sender.mails_to_send))
        self.assertEqual('david.vlaminck@mow.vlaanderen.be', sender.mails_to_send[0].receiver)
        self.assertEqual('test report title', sender.mails_to_send[0].report_name)
        self.assertEqual(1, sender.mails_to_send[0].count)

    def test_wijziging_different_values_two_receivers(self):
        sender = MailSender()
        self.assertListEqual([], sender.mails_to_send)
        report = DQReport(name='test report', title='test report title', spreadsheet_id='testsheetId')
        report.send_mails(sender=sender, named_range=[['david.vlaminck@mow.vlaanderen.be', 'Wijziging', ''],
                                                      ['second@mow.vlaanderen.be', 'Wijziging', '']],
                          previous_result=0, result=1)
        self.assertEqual(2, len(sender.mails_to_send))
        self.assertEqual('david.vlaminck@mow.vlaanderen.be', sender.mails_to_send[0].receiver)
        self.assertEqual('second@mow.vlaanderen.be', sender.mails_to_send[1].receiver)

    @mock.patch(f'{DQReport.__name__}.date', wraps=datetime)
    def test_daily_only_half_a_day_passed(self, mock_date):
        mock_date.today.return_value = date(2022, 1, 1)

        sender = MailSender()
        self.assertListEqual([], sender.mails_to_send)
        report = DQReport(name='test report', title='test report title', spreadsheet_id='testsheetId')
        report.send_mails(sender=sender, named_range=[['david.vlaminck@mow.vlaanderen.be', 'Dagelijks', '2022-01-01 01:00:00']],
                          previous_result=0, result=1)
        self.assertListEqual([], sender.mails_to_send)

    @mock.patch(f'{DQReport.__name__}.date', wraps=datetime)
    def test_daily_one_day_passed(self, mock_date):
        mock_date.today.return_value = date(2022, 1, 2)

        sender = MailSender()
        self.assertListEqual([], sender.mails_to_send)
        report = DQReport(name='test report', title='test report title', spreadsheet_id='testsheetId')
        report.send_mails(sender=sender,
                          named_range=[['david.vlaminck@mow.vlaanderen.be', 'Dagelijks', '2022-01-01 01:00:00']],
                          previous_result=0, result=1)
        self.assertEqual(1, len(sender.mails_to_send))

    # last sent value <> null
    # wekelijks
    # maandelijks
    # unsupported value (syntax error)

    # same receiver

