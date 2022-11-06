# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import api, models, fields, _
from datetime import datetime
import logging
import base64

_logger = logging.getLogger(__name__)


class ShippingFileType(models.Model):
    _name = 'servoo.shipping.file.type'

    name = fields.Char('Name', required=True)
    description = fields.Char('Description')
    sequence_code = fields.Char('Sequence Code')


def _populate_manifest_structure(file):
    header = """<?xml version="1.0" encoding="utf-8"?>
<DOCUMENT>
<TYPE_DOCUMENT>Z29</TYPE_DOCUMENT>
<TYPE_MESSAGE>CUSCAR</TYPE_MESSAGE>
<ETAT>Z01</ETAT>
<REFERENCE_DOSSIER>
<NUMERO_DOSSIER></NUMERO_DOSSIER>
<NUMERO_DEMANDE></NUMERO_DEMANDE>
<NUMERO_MESSAGE></NUMERO_MESSAGE>
<UTILISATEUR>MAKITA SERGE</UTILISATEUR>
</REFERENCE_DOSSIER>
<ROUTAGE>
<EMETTEUR>APM.SA</EMETTEUR>
<DESTINATAIRE>PAD1</DESTINATAIRE>
</ROUTAGE>
<MANIFESTE>
<GEN_CODE_MANIFESTE></GEN_CODE_MANIFESTE>
<GEN_DATA>
  <GEN_CODE_MANIFESTE></GEN_CODE_MANIFESTE>
  <GEN_CODE_BUREAU>%s</GEN_CODE_BUREAU>
  <GEN_DATE_EMISSION>%s</GEN_DATE_EMISSION>
  <GEN_SENS_MANIFESTE>%s</GEN_SENS_MANIFESTE>
  <GEN_NUMERO_VOYAGE>%s</GEN_NUMERO_VOYAGE>
  <GEN_NAVIRE>%s</GEN_NAVIRE>
  <GEN_ANNEE_TRANSPORT>%s</GEN_ANNEE_TRANSPORT>
  <GEN_JAUGE_BRUTE>%s</GEN_JAUGE_BRUTE>
  <GEN_JAUGE_NETTE>%s</GEN_JAUGE_NETTE>
  <GEN_CAPITAINE>%s</GEN_CAPITAINE>
  <GEN_CODE_CONSIGNATAIRE>12610</GEN_CODE_CONSIGNATAIRE>
  <GEN_NOM_CONSIGNATAIRE>AGENCE DE PRESTATIONS MARITIMES</GEN_NOM_CONSIGNATAIRE>
  <GEN_CODE_ARMATEUR></GEN_CODE_ARMATEUR>
  <GEN_NOM_ARMATEUR>%s</GEN_NOM_ARMATEUR>
  <GEN_CODE_AFFRETEUR></GEN_CODE_AFFRETEUR>
  <GEN_NOM_AFFRETEUR>%s</GEN_NOM_AFFRETEUR>
  <GEN_NOM_PAVILLON>%s</GEN_NOM_PAVILLON>
</GEN_DATA>
<CONNAISSEMENT_MARCHANDISES>
    """ % (file.port_arrival_departure.code if file.port_arrival_departure else '',
           file.date_arrival_departure or '',
           'IMPORT' if file.operation_type == 'arrival' else 'EXPORT',
           file.voyage_number or '',
           file.vessel.name or '',
           datetime.now().year,
           file.grt or '',
           file.nrt or '',
           file.name_of_master or '',
           file.shipowner_id.name or '',
           file.charterer_id.name or '',
           file.flag_vessel.name or ''
           )
    bl_content = ""
    counter = 0
    for bl in file.bl_ids:
        counter += 1
        bl_content += """<CONNAISSEMENT_MARCHANDISE>
    <CNS_CODE_CONNAISSEMENT>%s</CNS_CODE_CONNAISSEMENT>
    <CNS_CODE_BUREAU />
    <CNS_NUMERO_VOYAGE></CNS_NUMERO_VOYAGE>
    <CNS_NUMERO_LIGNE>%s</CNS_NUMERO_LIGNE>
    <CNS_NUMERO_SOUS_LIGNE />
    <CNS_TYPE_CONNAISSEMENT>CO2</CNS_TYPE_CONNAISSEMENT>
    <CNS_NATURE_TITRE_TRANSPORT>23</CNS_NATURE_TITRE_TRANSPORT>
    <CNS_CHARGEUR />
    <CNS_CODE_EXPEDITEUR />
    <CNS_EXPEDITEUR>%s</CNS_EXPEDITEUR>
    <CNS_ADR1_EXPEDITEUR>%s</CNS_ADR1_EXPEDITEUR>
    <CNS_ADR2_EXPEDITEUR>%s</CNS_ADR2_EXPEDITEUR>
    <CNS_ADR3_EXPEDITEUR />
    <CNS_ADR4_EXPEDITEUR />
    <CNS_CODE_DESTINATAIRE />
    <CNS_DESTINATAIRE>%s</CNS_DESTINATAIRE>
    <CNS_ADR1_DESTINATAIRE />
    <CNS_ADR2_DESTINATAIRE />
    <CNS_ADR3_DESTINATAIRE />
    <CNS_ADR4_DESTINATAIRE />
    <CNS_PROVENANCE>%s</CNS_PROVENANCE>
    <CNS_LIEU_CHARGEMENT></CNS_LIEU_CHARGEMENT>
    <CNS_NOMBRE_CONTENEURS></CNS_NOMBRE_CONTENEURS>
    <CNS_TYPE_COLIS />
    <CNS_MARQUE1_COLIS />
    <CNS_MARQUE2_COLIS />
    <CNS_MARQUE3_COLIS />
    <CNS_MARQUE4_COLIS />
    <CNS_MARQUE5_COLIS />
    <CNS_MARQUE6_COLIS />
    <CNS_MARQUE7_COLIS />
    <CNS_MARQUE8_COLIS />
    <CNS_MARQUE9_COLIS />
    <CNS_MARQUE10_COLIS />
    <CNS_DESCRIPTION_MARCH1>%s</CNS_DESCRIPTION_MARCH1>
    <CNS_POIDS_COLIS>%s</CNS_POIDS_COLIS>
    <DETAIL_MARCHANDISE>
        """ % (
            bl.name or '',
            counter,
            bl.shipper_id.name or '',
            bl.shipper_id.street or '',
            bl.shipper_id.street2 or '',
            bl.consignee_id.name or '',
            bl.loading_port.name + ',' + bl.loading_port.country_id.name,
            bl.cargo_description or '',
            bl.cargo_weight or ''
        )
        good_content = ''
        for good in bl.good_ids:
            good_content += """<MARCHANDISE>
            <TYPE_COLIS></TYPE_COLIS>
            <MARQUE_COLIS></MARQUE_COLIS>
            <DESCRIPTION1>%s</DESCRIPTION1>
            <DESCRIPTION2 />
            <POIDS_COLIS>%s</POIDS_COLIS>
            <VOLUME_COLIS>%s</VOLUME_COLIS>
            <NOMBRE_COLIS>%s</NOMBRE_COLIS>
      </MARCHANDISE>
            """ % (
                good.name or '',
                good.gross_weight or '',
                good.volume or '',
                good.quantity or ''
            )
        if not good_content:
            good_content = "<MARCHANDISE />"
        bl_content += good_content + """</DETAIL_MARCHANDISE>
    </CONNAISSEMENT_MARCHANDISE>
        """
    if not bl_content:
        bl_content = "<CONNAISSEMENT_MARCHANDISE />"
    content = header + bl_content + """</CONNAISSEMENT_MARCHANDISES>
</MANIFESTE>
</DOCUMENT>
    """
    return content


class ShippingFile(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'servoo.shipping.file'
    _order = 'id desc'

    file_type_id = fields.Many2one('servoo.shipping.file.type', 'File Type', required=True)
    name = fields.Char(string='Reference', required=True, index=True, default=lambda self: _('New'), copy=False)
    shipping_pda_id = fields.Many2one('servoo.shipping.pda', 'PDA')
    partner_id = fields.Many2one('res.partner', 'Client', required=True)
    shipowner_id = fields.Many2one('res.partner', 'Shipowner')
    charterer_id = fields.Many2one('res.partner', 'Charterer')
    formality_line = fields.One2many('servoo.shipping.formality', 'file_id', string='Formality Lines',
                                     auto_join=True, index=True, copy=True)
    document_ids = fields.One2many('servoo.shipping.document', 'file_id', string='Documents', auto_join=True,
                                   copy=True)

    parent_id = fields.Many2one('servoo.shipping.file', 'Parent')
    child_ids = fields.One2many('servoo.shipping.file', 'parent_id', string='Sub-file', auto_join=True, copy=True)
    invoice_count = fields.Integer(compute="_get_invoiced", string='Invoices')
    user_id = fields.Many2one('res.users', 'User id')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('done', 'Done'),
        ('cancel', 'Cancel')
    ], string='Status', default='draft')
    # FAL 1: General Information
    vessel = fields.Many2one('res.transport.means', string="Vessel")
    loa = fields.Float('LOA', digits=(6, 3))
    beam = fields.Float('Beam', digits=(6, 3), help='Largeur')
    summer_draft = fields.Float('Summer draft', digits=(6, 3))
    vessel_volume = fields.Float('Vessel Volume', digits=(6, 3))
    nrt = fields.Float('NRT', digits=(6, 3), help='NRT')
    grt = fields.Float('GRT', digits=(12, 4), required=False, tracking=6)
    cbm_vessel = fields.Float('CBM Vessel', digits=(12, 4), required=False, tracking=6)
    operation_type = fields.Selection([('arrival', 'Arrival'), ('departure', 'Departure')])
    imo_number = fields.Char('IMO Number')
    call_sign = fields.Char('Call Sign')
    name_of_master = fields.Char('Name of master')
    voyage_number = fields.Char('Travel Number')
    port_arrival_departure = fields.Many2one('res.locode', 'Port of loading/discharge')
    port_previous_next = fields.Many2one('res.locode', 'Last Port/Next Port')
    date_arrival_departure = fields.Datetime('Date and time of arrival/departure')
    flag_vessel = fields.Many2one('res.country', 'Flag')
    gross_weight = fields.Float('Cargo gross tonnage (kg)', digits=(12, 3))
    net_weight = fields.Float('Cargo net tonnage (kg)', digits=(12, 3))
    travel_description = fields.Text('Particulars of voyage')
    goods_description = fields.Text('Description of goods')

    bl_ids = fields.One2many('servoo.shipping.bl', 'shipping_file_id', string='Bill of loading', index=True)
    # crew_count = fields.Integer('Crew Count', compute="_get_crew_count")
    # passenger_count = fields.Integer('Passenger Count', compute="_get_passenger_count")
    # FAL 2: Cargo Declaration
    good_ids = fields.One2many('servoo.shipping.good', 'file_id', string='Goods',
                               auto_join=True, index=True, copy=True)
    container_ids = fields.One2many('servoo.shipping.container', 'file_id', string='Containers',
                                    auto_join=True, index=True, copy=True)
    # FAL 3: Ship's stores Declaration
    store_ids = fields.One2many('servoo.shipping.ship.store', 'file_id', "Ship's stores")
    # FAL 4: Crew's effects Declaration
    crew_effect_ids = fields.One2many('servoo.shipping.crew.effect', 'file_id', "Crew's effects")
    # FAL 5: Crew List
    crew_ids = fields.One2many('servoo.shipping.crew', 'file_id', 'Crew List')
    # FAL 6: Passenger List
    passenger_ids = fields.One2many('servoo.shipping.passenger', 'file_id', 'Passengers List')
    # FAL 7: Dangerous Goods Manifest
    dangerous_good_ids = fields.One2many('servoo.shipping.dangerous.good', 'file_id', 'Dangerous Goods')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', _('This reference must be unique!'))
    ]

    def name_get(self):
        result = []
        for pda in self:
            name = pda.name + (pda.vessel and (' - ' + pda.vessel.name) or '')
            result.append((pda.id, name))
        return result

    def _get_invoiced(self):
        invoice = self.env['account.move']
        for record in self:
            record.invoice_count = invoice.search_count([('invoice_origin', '=', record.name)])

    # def _get_crew_count(self):
    #     for record in self:
    #         record.crew_count = len(record.crew_ids)
    #
    # def _get_passenger_count(self):
    #     for record in self:
    #         record.passenger_count = len(record.passenger_ids)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    'servoo.shipping.file') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('servoo.shipping.file') or _('New')
        return super().create(vals)

    def action_draft(self):
        return self.write({'state': 'draft'})

    def action_cancel(self):
        return self.write({'state': 'cancel'})

    def action_done(self):
        datas = {'state': 'done'}
        for item in self:
            if not item.date_end:
                datas['date_end'] = datetime.now()
        return self.write(datas)

    def action_open(self):
        return self.write({'state': 'open'})

    def return_action_to_open(self):
        """ This opens the xml view specified in xml_id for the current file """
        self.ensure_one()
        xml_id = self.env.context.get('xml_id')
        if xml_id:
            res = self.env['ir.actions.act_window']._for_xml_id('%s' % xml_id)
            res.update(
                context=dict(self.env.context, default_file_id=self.id, group_by=False),
                domain=[('invoice_origin', '=', self.name)]
            )
            return res
        return False

    def _prepare_invoice(self):
        self.ensure_one()
        journal = self.env['account.move'].with_context(default_move_type='out_invoice')._get_default_journal()
        if not journal:
            raise UserError(
                _('Please define an accounting sales journal for the company %s (%s).', self.company_id.name,
                  self.company_id.id))

        invoice_vals = {
            'move_type': 'out_invoice',
            'user_id': self.user_id.id,
            'invoice_user_id': self.user_id.id,
            'partner_id': self.partner_id.id,
            'partner_shipping_id': self.partner_id.id,
            'journal_id': journal.id,  # company comes from the journal
            'invoice_origin': self.name,
            'invoice_line_ids': []
        }
        return invoice_vals

    def _get_invoiceable_lines(self):
        invoiceable_line_ids = []
        for line in self.formality_line:
            invoiceable_line_ids.append(line.id)
        return self.env['servoo.shipping.formality'].browse(invoiceable_line_ids)

    def create_invoices(self):
        if not self.env['account.move'].check_access_rights('create', False):
            try:
                self.check_access_rights('write')
                self.check_access_rule('write')
            except AccessError:
                return self.env['account.move']
        # 1) Create invoices.
        invoice_vals_list = []
        for file in self:
            invoice_vals = file._prepare_invoice()
            invoiceable_lines = file._get_invoiceable_lines()
            invoice_line_vals = []
            for line in invoiceable_lines:
                invoice_line_vals.append(
                    (0, 0, {
                        'name': line.name,
                        'product_id': line.service_id.id,
                        'quantity': 1.0,
                        'price_unit': line.amount,
                    }),
                )
            invoice_vals['invoice_line_ids'] += invoice_line_vals
            invoice_vals_list.append(invoice_vals)
        moves = self.env['account.move'].sudo().with_context(default_move_type='out_invoice').create(invoice_vals_list)
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        if len(moves) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(moves) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = moves.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        context = {
            'default_move_type': 'out_invoice',
        }
        if len(self) == 1:
            context.update({
                'default_partner_id': self.partner_id.id,
                'default_partner_shipping_id': self.partner_id.id,
                'default_invoice_origin': self.name,
                'default_user_id': self.user_id.id,
            })
        action['context'] = context
        return action

    @api.onchange('shipping_pda_id')
    def onchange_shipping_pda(self):
        if self.shipping_pda_id:
            self.vessel = self.shipping_pda_id.vessel_id.id
            if not self.partner_id:
                self.partner_id = self.shipping_pda_id.partner_id.id
            self.voyage_number = self.shipping_pda_id.voyage_number
            self.beam = self.shipping_pda_id.beam
            self.loa = self.shipping_pda_id.loa
            self.summer_draft = self.shipping_pda_id.summer_draft
            self.vessel_volume = self.shipping_pda_id.vessel_volume
            self.nrt = self.shipping_pda_id.nrt
            self.grt = self.shipping_pda_id.grt
            self.cbm_vessel = self.shipping_pda_id.cbm_vessel
            self.gross_weight = self.shipping_pda_id.tonnage_of_goods

    # TO DO: Faire un cron pour supprimer les piece jointes créés lors de la génération du fichier xml
    def generate_xml_file(self):
        for record in self:
            xml_content = _populate_manifest_structure(record)
            result = bytes(xml_content, 'utf8')
            base_url = self.env['ir.config_parameter'].get_param('web.base.url')
            attachment_obj = self.env['ir.attachment']
            name = record.name + '-' + record.vessel.name + ".XML"
            attachment_id = attachment_obj.create(
                {'name': name,
                 'store_fname': name,
                 'db_datas': result,
                 'type': 'binary',
                 'res_model': 'servoo.shipping.file',
                 'mimetype': "application/xml"})
            download_url = '/web/content/' + str(attachment_id.id) + '?download=true'
            return {
                "type": "ir.actions.act_url",
                "url": str(base_url) + str(download_url),
                "target": "new",
            }


