from odoo import http
from odoo.http import request
import io
import xlsxwriter
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

class ExcelReportController(http.Controller):

    @http.route('/online_course/event_attendees_report', type='http', auth='user')
    def generate_event_attendees_report(self, **kw):
        # Dapatkan ID acara dari parameter URL
        event_id = kw.get('event_id')
        if not event_id:
            return http.request.render('online_course.error_page')

        # Logika untuk menghasilkan laporan Excel berdasarkan ID acara
        # Misalnya, menggunakan model event.event dan event.registration untuk mendapatkan data yang diperlukan

        # Buat workbook dan worksheet baru
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        # Tulis header pada worksheet
        header = ['Nama','Registration Date', 'Email', 'Phone']
        for col, column_name in enumerate(header):
            worksheet.write(0, col, column_name)

        # Dapatkan data peserta yang menghadiri acara dengan ID yang diberikan
        event = request.env['event.event'].browse(int(event_id))
        attendees = event.registration_ids.filtered(lambda r: r.state == 'open')

        row = 1
        for attendee in attendees:
            worksheet.write(row, 0, attendee.partner_id.name)
            worksheet.write(row, 1, attendee.date_open)
            worksheet.write(row, 2, attendee.partner_id.email)
            worksheet.write(row, 3, attendee.partner_id.phone)

            row += 1

        # Simpan workbook ke output
        workbook.close()
        output.seek(0)

        # Kembalikan response dengan file Excel
        filename = 'event_attendees_report.xlsx'
        headers = [
            ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('Content-Disposition', http.content_disposition(filename))
        ]
        return request.make_response(output, headers=headers)
    
class PDFReportController(http.Controller):

    @http.route('/online_course/event_attendees_report_pdf', type='http', auth='user')
    def generate_event_attendees_report_pdf(self, **kw):
        # Dapatkan ID acara dari parameter URL
        event_id = kw.get('event_id')
        if not event_id:
            return http.request.render('online_course.error_page')

        # Logika untuk menghasilkan laporan PDF berdasarkan ID acara
        # Misalnya, menggunakan model event.event dan event.registration untuk mendapatkan data yang diperlukan

        # Dapatkan data peserta yang menghadiri acara dengan ID yang diberikan
        event = request.env['event.event'].browse(int(event_id))
        attendees = event.registration_ids.filtered(lambda r: r.state == 'open')

        # Buat objek PDF
        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=letter)

        # Buat tabel untuk data peserta
        data = [['Nama', 'Registration Date', 'Email', 'Phone']]
        for attendee in attendees:
            data.append([
                attendee.partner_id.name,
                attendee.date_open,
                attendee.partner_id.email,
                attendee.partner_id.phone
            ])

        # Konfigurasi tabel
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.gray),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ]))

        # Tambahkan tabel ke dokumen PDF
        elements = [table]

        # Buat dokumen PDF
        doc.build(elements)

        # Kembalikan response dengan file PDF
        filename = 'event_attendees_report.pdf'
        headers = [
            ('Content-Type', 'application/pdf'),
            ('Content-Disposition', http.content_disposition(filename))
        ]
        output.seek(0)
        return request.make_response(output, headers=headers)
