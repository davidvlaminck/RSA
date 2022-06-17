import unittest
from datetime import datetime, date
from unittest import mock

from DQReport import DQReport
from MailSender import MailSender


class DQReportTests(unittest.TestCase):
    def test_empty_range(self):
        sender = MailSender()
        self.assertListEqual([], sender.mails)
        report = DQReport(name='test report', title='test report title', spreadsheet_id='testsheetId')
        report.send_mails(sender=sender, named_range=[[]], previous_result=-1, result=-1)
        self.assertListEqual([], sender.mails)

    def test_wijziging_same_value_one_receiver(self):
        sender = MailSender()
        self.assertListEqual([], sender.mails)
        report = DQReport(name='test report', title='test report title', spreadsheet_id='testsheetId')
        report.send_mails(sender=sender, named_range=[['david.vlaminck@mow.vlaanderen.be', 'Wijziging', '']], previous_result=0, result=0)
        self.assertListEqual([], sender.mails)

    def test_wijziging_different_values_one_receiver(self):
        sender = MailSender()
        self.assertListEqual([], sender.mails)
        report = DQReport(name='test report', title='test report title', spreadsheet_id='testsheetId')
        report.send_mails(sender=sender, named_range=[['david.vlaminck@mow.vlaanderen.be', 'Wijziging', '']], previous_result=0, result=1)
        self.assertEqual(1, len(sender.mails))
        self.assertEqual('david.vlaminck@mow.vlaanderen.be', sender.mails[0].receiver)
        self.assertEqual('test report title', sender.mails[0].report_name)
        self.assertEqual(1, sender.mails[0].count)

    def test_wijziging_different_values_two_receivers(self):
        sender = MailSender()
        self.assertListEqual([], sender.mails)
        report = DQReport(name='test report', title='test report title', spreadsheet_id='testsheetId')
        report.send_mails(sender=sender, named_range=[['david.vlaminck@mow.vlaanderen.be', 'Wijziging', ''],
                                                      ['second@mow.vlaanderen.be', 'Wijziging', '']], previous_result=0, result=1)
        self.assertEqual(2, len(sender.mails))
        self.assertEqual('david.vlaminck@mow.vlaanderen.be', sender.mails[0].receiver)
        self.assertEqual('second@mow.vlaanderen.be', sender.mails[1].receiver)

    @mock.patch(f'{DQReport.__name__}.date', wraps=datetime)
    def test_daily_only_half_a_day_passed(self, mock_date):
        mock_date.today.return_value = date(2022, 1, 1)

        sender = MailSender()
        self.assertListEqual([], sender.mails)
        report = DQReport(name='test report', title='test report title', spreadsheet_id='testsheetId')
        report.send_mails(sender=sender, named_range=[['david.vlaminck@mow.vlaanderen.be', 'Dagelijks', '2022-01-01 01:00:00']], previous_result=0, result=1)
        self.assertListEqual([], sender.mails)

    @mock.patch(f'{DQReport.__name__}.date', wraps=datetime)
    def test_daily_one_day_passed(self, mock_date):
        mock_date.today.return_value = date(2022, 1, 2)

        sender = MailSender()
        self.assertListEqual([], sender.mails)
        report = DQReport(name='test report', title='test report title', spreadsheet_id='testsheetId')
        report.send_mails(sender=sender, named_range=[['david.vlaminck@mow.vlaanderen.be', 'Dagelijks', '2022-01-01 01:00:00']], previous_result=0, result=1)
        self.assertEqual(1, len(sender.mails))

    # last sent value <> null
    # wekelijks
    # maandelijks
    # unsupported value (syntax error)

    # same receiver

