from re import T
from INSLPCModel.fields import Fields
from INSLPCModel.Model import INSAPP, Item, Model
from INSLPCModel.Statements import *
import json, notifiers, random
import datetime
import decimal

btn_list = []#'TR_LABEL', 'DELETE_BUTTON_2','ADD_BUTTON_2','DELETE_BUTTON','ADD_BUTTON','ADD_LANGUAGE_BTN']


app = INSAPP(
    app_name= 'INS Production Plan',
    app_version = '1.0',
    app_file_type = 'inspp',
    app_logo = 'main.png',
    translateable_labels_and_buttons = btn_list,

    )



######################################################################################################
#################################### Repository ######################################################
######################################################################################################



class Repository(Model):
    ui_list = app.UI.repositories_list
    
    add_button          = app.UI.add_repository
    delete_button       = app.UI.delete_repository
    view_name           = 'f"{item.Name}"'

    fields = {

        'Name'                     : Fields.CharField(),
        'Code'                     : Fields.CharField(),
        'Manager'                  : Fields.CustomListField(list_name='repo_manager'),
        'extra_info'               : Fields.ManyToManyField(subfields={
            'name'                 : Fields.CharField(),
            'value'                : Fields.CharField(),
                },
            view_name = """ f'{data["name"]}:  {data["value"]}' """,
            
            ),
        'extra_records'            : Fields.ManyToManyField(subfields={
            'Record_Name'          : Fields.CharField(),
            'data'                 : Fields.ManyToManyField(subfields={
                'Title'            : Fields.CharField(),
                'Info'             : Fields.TextField()
                },
                view_name = """f'{data["Title"]}'""",
                single_view = True)
            },
            view_name = """f'{data["Record_Name"]}'"""
            )
        
    }

######################################################################################################
#################################### Raw_Material ####################################################
######################################################################################################



class Raw_material(Model):


    #######################################################################
    ######################## FILTERS ######################################
    #######################################################################

    def Low_Quantity_Materials_Filter(self, objects, **kwagrs):
        LQM_list = []
        for obj in objects:
            if obj.Low_Quantity_Warning:
                current_quantity    = self.Get_Base_Quantity(obj.Unit, obj.Quantity)
                Low_quantity        = self.Get_Base_Quantity(obj.Minimum_Unit, obj.Minimum_Quantity)
                if current_quantity <= Low_quantity:
                    LQM_list.append(obj)

        return LQM_list


    def Quantity_Less_Than(self, objects, **kwagrs):
        QLT_list = []
        value = kwagrs.get('value')
        if value != None and len(value.split(' ')) >= 2:
            try:
                quantity    = float(value.split(' ')[0].replace(',','.'))
                unit        = value.split(' ')[1].upper()
                value_base_quantity = self.Get_Base_Quantity(unit, quantity)
                for obj in objects:
                    obj_base_quantity = self.Get_Base_Quantity(obj.Unit, obj.Quantity)
                    if obj_base_quantity < value_base_quantity : 
                        QLT_list.append(obj)
            except:
                pass
        return QLT_list

    def Quantity_More_Than(self, objects, **kwagrs):
        QMT_list = []
        value = kwagrs.get('value')
        if value != None and len(value.split(' ')) >= 2:
            try:
                quantity    = float(value.split(' ')[0].replace(',','.'))
                unit        = value.split(' ')[1].upper()
                
                value_base_quantity = self.Get_Base_Quantity(unit, quantity)
                for obj in objects:
                    obj_base_quantity = self.Get_Base_Quantity(obj.Unit, obj.Quantity)
                    if obj_base_quantity > value_base_quantity : 
                        QMT_list.append(obj)
            except:
                pass
        return QMT_list


    def Low_Quantity_Warning_Active(self, objects, **kwagrs):
        LQWA_list = []
        for obj in objects:
            if obj.Low_Quantity_Warning:
                LQWA_list.append(obj)

        return LQWA_list

    #######################################################################
    ######################## SIGNALS ######################################
    #######################################################################
    
    def dlr(self,item, data ):
        print('on edit   ',item)
        return False

    def add_input(data, main_ui):
        print(main_ui)
        #if main_ui.item_obj.Material_type != str:
        #    quantity_data = get_perfect_unit(data['Quantity'], main_ui.item_obj.Material_type.ui_field.currentText())
            

        #else:
        #    quantity_data = get_perfect_unit(data['Quantity'], main_ui.item_obj.Material_type)
        
        #main_ui.Quantity.setValue(quantity_data[0])
        #main_ui.Unit.setCurrentText(quantity_data[1])
        
    def on_edit(self, old_data, new_data):
        edited_item = self.get(id = old_data['id'])
        
        old_inputs      = json.loads(old_data['Materials_Inputs'].replace("'",'"'))
        old_outputs     = json.loads(old_data['Materials_Outputs'].replace("'",'"'))
        old_reword      = json.loads(old_data['rework'].replace("'",'"'))
        old_ruin        = json.loads(old_data['Ruin'].replace("'",'"'))
        
        new_inputs      = json.loads(new_data['Materials_Inputs'].replace("'",'"'))
        new_outputs     = json.loads(new_data['Materials_Outputs'].replace("'",'"'))
        new_reword      = json.loads(new_data['rework'].replace("'",'"'))
        new_ruin        = json.loads(new_data['Ruin'].replace("'",'"'))

        added_ruin      = [i for i in new_ruin if i not in old_ruin and i['Quantity_Withdrawal'] ]
        removed_ruin    = [i for i in old_ruin if i not in new_ruin and i['Quantity_Withdrawal'] ]

        added_reword    = [i for i in new_reword if i not in old_reword and i['Quantity_Reword'] ]
        removed_reword  = [i for i in old_reword if i not in new_reword and i['Quantity_Reword'] ]

        added_inputs    = [i for i in new_inputs if i not in old_inputs]
        removed_inputs  = [i for i in old_inputs if i not in new_inputs]

        added_outputs   = [i for i in new_outputs if i not in old_outputs]
        removed_outputs = [i for i in old_outputs if i not in new_outputs]

        total_changed_quantity = sum( [ self.Get_Base_Quantity( i['Unit'], i['Quantity']) for i in added_inputs ] ) 
        total_changed_quantity += sum( [ self.Get_Base_Quantity( i['Unit'], i['Quantity']) for i in added_reword ] )
        total_changed_quantity += sum( [ self.Get_Base_Quantity( i['Unit'], i['Quantity']) for i in removed_outputs ] )
        total_changed_quantity += sum( [ self.Get_Base_Quantity( i['Unit'], i['Quantity']) for i in removed_ruin ] )

        total_changed_quantity -= sum( [ self.Get_Base_Quantity( i['Unit'], i['Quantity']) for i in removed_inputs ] )
        total_changed_quantity -= sum( [ self.Get_Base_Quantity( i['Unit'], i['Quantity']) for i in added_outputs ] )
        total_changed_quantity -= sum( [ self.Get_Base_Quantity( i['Unit'], i['Quantity']) for i in added_ruin ] )
        total_changed_quantity -= sum( [ self.Get_Base_Quantity( i['Unit'], i['Quantity']) for i in removed_reword ] )
                                    

        new_material_base_quantity =  self.Get_Base_Quantity( edited_item.Unit, edited_item.Quantity ) + total_changed_quantity
        edited_item.Quantity = self.Get_Quantity_for_Static_Unit(edited_item.Unit , new_material_base_quantity)
        edited_item.save()

        if edited_item.Low_Quantity_Warning:
            if self.Get_Base_Quantity(edited_item.Minimum_Unit, edited_item.Minimum_Quantity ) >= self.Get_Base_Quantity(edited_item.Unit, edited_item.Quantity):
                pass
                #notifiers.Notification( self.INSApp.translate("Warning")  ,self.INSApp.translate("You have low quantity of") + str(edited_item) ,self.INSApp.app_logo ).show()


    def Get_Base_Quantity(self, unit, quantity):
        quantity = float(quantity)
        cov = { 'MG': 1000,'CG':100,'DG':10,'G':1,
                'DAG': 0.1,'HG':0.01,'KG':0.001,'T':0.0001,
                
                'ML': 1000,'CL':100,'DL':10,'L':1,
                'DAL': 0.1,'HL':0.01,'KL':0.001,'T':0.0001}
        quantity /= cov[unit.upper()]
        return quantity

    def Get_Quantity_for_Static_Unit( self, unit, quantity):
        quantity = float(quantity)
        cov = { 'MG': 1000,'CG':100,'DG':10,'G':1,
                'DAG': 0.1,'HG':0.01,'KG':0.001,'T':0.0001,
                
                'ML': 1000,'CL':100,'DL':10,'L':1,
                'DAL': 0.1,'HL':0.01,'KL':0.001,'T':0.0001}
        quantity *= cov[unit.upper()]
        return quantity

    #######################################################################
    ######################## GRAPH ########################################
    #######################################################################


 
    
    def show_inputs_graph(item):
        if type(item.Materials_Inputs) == str:
            item.Materials_Inputs = json.loads(item.Materials_Inputs)
        return get_graph_data_type_1(item, item.Materials_Inputs, info_form = '{} | {} '+ app.translate('Added'))

    def show_outputs_graph(item):
        if type(item.Materials_Outputs) == str:
            item.Materials_Outputs = json.loads(item.Materials_Outputs)
        return get_graph_data_type_1(item, item.Materials_Outputs, info_form = '{} | {} '+ app.translate('Used') )

    def show_reword_graph(item):
        if type(item.rework) == str:
            item.rework = json.loads(item.rework)
        return get_graph_data_type_1(item, item.rework, info_form = '{} | {} '+ app.translate('Used') )


    def show_ruins_graph(item):
        if type(item.Ruin) == str:
            item.Ruin = json.loads(item.Ruin)
        return get_graph_data_type_1(item, item.Ruin, info_form = '{} | {} '+ app.translate('Used') )


    def rework_resions_pie_data(item, extra_data):
        date_from   = datetime.date.fromisoformat(extra_data.get('From'))
        date_to     = datetime.date.fromisoformat(extra_data.get('To'))

        if type(item.rework) == str:
            item.rework = json.loads(item.rework.replace("'", '"'))

        data = {}
        biggest_quantity_reasion_value = 0
        biggest_quantity_reasion_label = ''
        for rework in item.rework:            
            rework_date = datetime.date.fromisoformat(rework['Date_and_time'])
            if date_from <= rework_date <= date_to:

                base_rework_quantity = Get_Base_Quantity(rework['Unit'], rework['Quantity'])
                if rework['Reason'] in data:
                    data[rework['Reason']] += base_rework_quantity
                
                else:
                    data[rework['Reason']] = base_rework_quantity


                if biggest_quantity_reasion_value < data[rework['Reason']] :
                    biggest_quantity_reasion_value = data[rework['Reason']]
                    GPU = get_perfect_unit(data[rework['Reason']], item.Material_type)
                    print(GPU)
                    biggest_quantity_reasion_label = f'⬆️: {rework["Reason"]}   { str(GPU[0]) + GPU[1] }'

        
        all_info = {
            'data': data,
            'extra_info' : biggest_quantity_reasion_label
        }

        return all_info

    def ruin_resions_pie_data(item, extra_data):
        date_from   = datetime.date.fromisoformat(extra_data.get('From'))
        date_to     = datetime.date.fromisoformat(extra_data.get('To'))

        if type(item.Ruin) == str:
            item.Ruin = json.loads(item.Ruin.replace("'", '"'))

        data = {}
        biggest_quantity_reasion_value = 0
        biggest_quantity_reasion_label = ''
        for Ruin in item.Ruin:

            ruin_date = datetime.date.fromisoformat(Ruin['Date_and_time'])
            if date_from <= ruin_date <= date_to:
                base_Ruin_quantity = Get_Base_Quantity(Ruin['Unit'], Ruin['Quantity'])
                if Ruin['Reason'] in data:
                    data[Ruin['Reason']] += base_Ruin_quantity
                
                else:
                    data[Ruin['Reason']] = base_Ruin_quantity


                if biggest_quantity_reasion_value < data[Ruin['Reason']] :
                    biggest_quantity_reasion_value = data[Ruin['Reason']]
                    GPU = get_perfect_unit(data[Ruin['Reason']], item.Material_type)
                    biggest_quantity_reasion_label = f'⬆️: {Ruin["Reason"]}   { str(GPU[0]) + GPU[1] }'

        
        all_info = {
            'data': data,
            'extra_info' : biggest_quantity_reasion_label
        }

        return all_info
    #######################################################################
    ######################## BUILD ########################################
    #######################################################################




    ui_list = app.UI.RawMaterials_UI_List
    
    add_button          = app.UI.RawMaterial_Add_Button
    delete_button       = app.UI.RawMaterial_Edit_Button
    view_name           = 'f"{item.Name}"'
    tooltip             = 'f"Code:{item.Code} <br> {item.Quantity} "'
    search_bar          = app.UI.RawMaterials_UI_SearchBar
    ui_list_info        = app.UI.raw_materials_list_info
    dashboard           = app.UI.RM_DashBoard

    def convert_quantity(ui, field, ui_loaded = True):
        if ui_loaded:
            cov = { 'MG': 1000,'CG':100,'DG':10,'G':1,
                    'DAG': 0.1,'HG':0.01,'KG':0.001,'T':0.0001,
                    
                    'ML': 1000,'CL':100,'DL':10,'L':1,
                    'DAL': 0.1,'HL':0.01,'KL':0.001,'T':0.0001}
            try:
                last_unit = getattr(field, 'last_unit')
                
                quantity =  Get_Base_Quantity(last_unit, ui.Quantity.value()) * cov[field.currentText()] 
                

                if - decimal.Decimal(str(quantity)).as_tuple().exponent < decimal.Decimal('2'):
                    ui.Quantity.setDecimals(2)
                else:
                    ui.Quantity.setDecimals( - decimal.Decimal(str(quantity)).as_tuple().exponent )

                
                ui.Quantity.setValue(quantity)
            
            except:
                pass

            setattr(field, 'last_unit', field.currentText())


    GRAPH_MODES = {
        'Inputs'    : show_inputs_graph,
        'Outputs'   : show_outputs_graph,
        'rework'    : show_reword_graph,
        'Ruin'      : show_ruins_graph,
    }

    last_year = datetime.date.today().replace(year = datetime.date.today().year - 1)
    next_year = datetime.date.today().replace(year = datetime.date.today().year + 1)

    PIE_GRAPH_MODES = {
        'rework_resions' : {
            'function': rework_resions_pie_data, 
            'extra_fields': {
                'From': Fields.DateField(default = last_year),
                'To': Fields.DateField(default = next_year)

            } 
        },
        'ruin_resions'      : {
            'function': ruin_resions_pie_data, 
            'extra_fields': {
                'From': Fields.DateField(default = last_year),
                'To': Fields.DateField(default = next_year)

            } 
        }
    }
    
    filters = {
        '#Low_Quantity_Materials:' : Low_Quantity_Materials_Filter,
        '#Quantity_Less_Than:' : Quantity_Less_Than,
        '#Quantity_More_Than:' : Quantity_More_Than,
        '#Low Quantity_Warning_Active:' : Low_Quantity_Warning_Active,
    }

    fields = {

        'Name'                     : Fields.CharField(),
        'Code'                     : Fields.CharField(),
        'Material_type'            : Fields.DictField(item_dict = {'solid':['MG','CG','DG','G','DAG','HG','KG','T'],'liquid':['ML','CL','DL','L','DAL','HL','KL'],'gas':['ML','CL','DL','L','DAL','HL','KL']} , subfields = ['Minimum_Unit','Unit']),
        'Quantity'                 : Fields.FloatField(editable = False),
        'Unit'                     : Fields.ListField(editable = False),
        'Low_Quantity_Warning'     : Fields.BoolField(),
        'Minimum_Quantity'         : Fields.FloatField(),
        'Minimum_Unit'             : Fields.ListField(),
        'Materials_Inputs'         : Fields.ManyToManyField(subfields = {
            'patch name'           : Fields.CharField(),
            'Quantity'             : Fields.FloatField(),
            'Unit'                 : Fields.ListField(data_from_DictField =  'Material_type'),
            'Date_and_time'        : Fields.DateField(),
            'source'               : Fields.CustomListField(list_name = 'materials_input_sources'),
            'repository'           : Fields.OneToOneField(model = 'Repository'),
            'Note'                 : Fields.TextField()},
            view_name = '''f"""{data['patch name']}  ({ data['Quantity'] } { data['Unit'] }) """'''  ,
            tooltip   = '''f"""{ data['Note'] }  """'''  ,
            on_add = add_input,
            before_edit = dlr
        
        ),
        'Materials_Outputs'        : Fields.ManyToManyField(subfields = {

            'Quantity'             : Fields.FloatField(),
            'Unit'                 : Fields.ListField(data_from_DictField =  'Material_type'),
            'Date_and_time'        : Fields.DateField(),
            'Note'                 : Fields.TextField()},
            view_name = '''f"""{ data['Quantity'] } { data['Unit'] } ({ data['Date_and_time'] }) """'''  ,
            tooltip   = '''f"""{ data['Note'] }  """'''  ,
            
            ),
        
        'rework'        : Fields.ManyToManyField(subfields = {

            'Quantity'             : Fields.FloatField(),
            'Unit'                 : Fields.ListField(data_from_DictField =  'Material_type'),
            'Date_and_time'        : Fields.DateField(),
            'Reason'               : Fields.CustomListField(list_name = 'RM_REWORD_REASON'),
            'Quantity_Reword'      : Fields.BoolField(),
            'Note'                 : Fields.TextField()},
            view_name = '''f"""{ data['Quantity'] } { data['Unit'] } ({ data['Date_and_time'] }) """'''  ,
            tooltip   = '''f"""{ data['Reason'] }  """'''  ,
            
            ),
        'Ruin'        : Fields.ManyToManyField(subfields = {

            'Quantity'             : Fields.FloatField(),
            'Unit'                 : Fields.ListField(data_from_DictField =  'Material_type'),
            'Date_and_time'        : Fields.DateField(),
            'Reason'               : Fields.CustomListField(list_name = 'RM_REWORD_REASON'),
            'Quantity_Withdrawal'  : Fields.BoolField(),
            'Note'                 : Fields.TextField()},
            view_name = '''f"""{ data['Quantity'] } { data['Unit'] } ({ data['Date_and_time'] }) """'''  ,
            tooltip   = '''f"""{ data['Reason'] }  """'''  ,
            
            ),
        'extra_info'                        : Fields.ManyToManyField(subfields={
            'name'                          : Fields.CharField(),
            'value'                         : Fields.CharField(),
                },
            view_name = """ f'{data["name"]}:  {data["value"]}' """,
            
            ),
        'extra_records'            : Fields.ManyToManyField(subfields={
            'Record_Name'          : Fields.CharField(),
            'data'                 : Fields.ManyToManyField(subfields={
                'Title'            : Fields.CharField(),
                'Info'             : Fields.TextField()
                },
                view_name = """f'{data["Title"]}'""",
                single_view = True)
            },
            view_name = """f'{data["Record_Name"]}'"""
            )
            }



######################################################################################################
#################################### Packaging_Material ##############################################
######################################################################################################



class Packaging_Material(Model):
    #######################################################################
    ######################## SIGNALS ######################################
    #######################################################################

    def on_edit(self, old_data, new_data):
        edited_item = self.get(id = old_data['id'])
        
        old_inputs      = json.loads(old_data['Materials_Inputs'])
        old_outputs     = json.loads(old_data['Materials_Outputs'])
        old_reword      = json.loads(old_data['rework'])
        old_ruin        = json.loads(old_data['Ruin'])

        new_inputs      = json.loads(new_data['Materials_Inputs'])
        new_outputs     = json.loads(new_data['Materials_Outputs'])
        new_reword      = json.loads(new_data['rework'])
        new_ruin        = json.loads(new_data['Ruin'])

        added_ruin      = [i for i in new_ruin if i not in old_ruin and i['Quantity_Withdrawal'] ]
        removed_ruin    = [i for i in old_ruin if i not in new_ruin and i['Quantity_Withdrawal'] ]

        added_reword    = [i for i in new_reword if i not in old_reword and i['Quantity_Reword'] ]
        removed_reword  = [i for i in old_reword if i not in new_reword and i['Quantity_Reword'] ]

        added_inputs    = [i for i in new_inputs if i not in old_inputs]
        removed_inputs  = [i for i in old_inputs if i not in new_inputs]

        added_outputs   = [i for i in new_outputs if i not in old_outputs]
        removed_outputs = [i for i in old_outputs if i not in new_outputs]

        total_changed_quantity =  sum(i['Quantity'] for i in added_inputs       )  
        total_changed_quantity += sum(i['Quantity'] for i in removed_outputs    )
        total_changed_quantity += sum(i['Quantity'] for i in added_reword       )
        total_changed_quantity += sum(i['Quantity'] for i in removed_ruin       )

        total_changed_quantity -= sum(i['Quantity'] for i in removed_inputs   )
        total_changed_quantity -= sum(i['Quantity'] for i in added_outputs    )
        total_changed_quantity -= sum(i['Quantity'] for i in removed_reword    )
        total_changed_quantity -= sum(i['Quantity'] for i in added_ruin    )

        edited_item.Quantity += total_changed_quantity
        edited_item.save()

        if edited_item.Low_Quantity_Warning:
            if edited_item.Minimum_Quantity >= edited_item.Quantity:
                pass
                #notifiers.Notification( self.INSApp.translate("Warning")  ,self.INSApp.translate("You have low quantity of") + str(edited_item) ,self.INSApp.app_logo ).show()

    #######################################################################
    ######################## FILTERS ######################################
    #######################################################################

    def Low_Quantity_Materials_Filter(self, objects, **kwagrs):
        LQM_list = []
        for obj in objects:
            if obj.Low_Quantity_Warning:
                current_quantity    = obj.Quantity
                Low_quantity        = obj.Minimum_Quantity
                if current_quantity <= Low_quantity:
                    LQM_list.append(obj)

        return LQM_list


    def Quantity_Less_Than(self, objects, **kwagrs):
        QLT_list = []
        value = kwagrs.get('value')
        if value != None:
            try:
                quantity    = float(value.replace(',','.'))
                for obj in objects:
                    obj_quantity = obj.Quantity
                    if obj_quantity < quantity : 
                        QLT_list.append(obj)
            except:
                pass
        return QLT_list

    def Quantity_More_Than(self, objects, **kwagrs):
        QLT_list = []
        value = kwagrs.get('value')
        if value != None:
            try:
                quantity    = float(value.replace(',','.'))
                for obj in objects:
                    obj_quantity = obj.Quantity
                    if obj_quantity > quantity : 
                        QLT_list.append(obj)
            except:
                pass
        return QLT_list


    def Low_Quantity_Warning_Active(self, objects, **kwagrs):
        LQWA_list = []
        for obj in objects:
            if obj.Low_Quantity_Warning:
                LQWA_list.append(obj)

        return LQWA_list

    #######################################################################
    ######################## GRAPH ########################################
    #######################################################################
    def show_inputs_graph(item):
        if type(item.Materials_Inputs) == str:
            item.Materials_Inputs = json.loads(item.Materials_Inputs)
        return get_graph_data_type_2(item, item.Materials_Inputs, info_form = '{} | {} '+ app.translate('Added'))

    def show_outputs_graph(item):
        if type(item.Materials_Outputs) == str:
            item.Materials_Outputs = json.loads(item.Materials_Outputs)
        return get_graph_data_type_2(item, item.Materials_Outputs, info_form = '{} | {} '+ app.translate('Used') )

    def show_reword_graph(item):
        if type(item.rework) == str:
            item.rework = json.loads(item.rework)
        return get_graph_data_type_2(item, item.rework, info_form = '{} | {} '+ app.translate('Used') )


    def show_ruins_graph(item):
        if type(item.Ruin) == str:
            item.Ruin = json.loads(item.Ruin)
        return get_graph_data_type_2(item, item.Ruin, info_form = '{} | {} '+ app.translate('Used') )


    def rework_resions_pie_data(item, extra_data):
        date_from   = datetime.date.fromisoformat(extra_data.get('From'))
        date_to     = datetime.date.fromisoformat(extra_data.get('To'))
        if type(item.rework) == str:
            item.rework = json.loads(item.rework.replace("'", '"'))

        data = {}
        biggest_quantity_reasion_value = 0
        biggest_quantity_reasion_label = ''
        for rework in item.rework:
            rework_date = datetime.date.fromisoformat(rework['Date_and_time'])
            if date_from <= rework_date <= date_to:
                base_rework_quantity = rework['Quantity']
                if rework['Reason'] in data:
                    data[rework['Reason']] += base_rework_quantity
                
                else:
                    data[rework['Reason']] = base_rework_quantity


                if biggest_quantity_reasion_value < data[rework['Reason']] :
                    biggest_quantity_reasion_value = data[rework['Reason']]
                    
                    biggest_quantity_reasion_label = f'⬆️: {rework["Reason"]}   { data[rework["Reason"]] }'

        
        all_info = {
            'data': data,
            'extra_info' : biggest_quantity_reasion_label
        }

        return all_info

    def ruin_resions_pie_data(item, extra_data):
        date_from   = datetime.date.fromisoformat(extra_data.get('From'))
        date_to     = datetime.date.fromisoformat(extra_data.get('To'))
        if type(item.Ruin) == str:
            item.Ruin = json.loads(item.Ruin.replace("'", '"'))

        data = {}
        biggest_quantity_reasion_value = 0
        biggest_quantity_reasion_label = ''
        for Ruin in item.Ruin:
            ruin_date = datetime.date.fromisoformat(Ruin['Date_and_time'])
            if date_from <= ruin_date <= date_to:
                base_Ruin_quantity = Ruin['Quantity']
                if Ruin['Reason'] in data:
                    data[Ruin['Reason']] += base_Ruin_quantity
                
                else:
                    data[Ruin['Reason']] = base_Ruin_quantity


                if biggest_quantity_reasion_value < data[Ruin['Reason']] :
                    biggest_quantity_reasion_value = data[Ruin['Reason']]
                    biggest_quantity_reasion_label = f'⬆️: {Ruin["Reason"]}   { data[Ruin["Reason"]] }'

        
        all_info = {
            'data': data,
            'extra_info' : biggest_quantity_reasion_label
        }

        return all_info



    ####################################################
    ###################Build############################
    ####################################################
    ui_list = app.UI.pm_list
    
    add_button          = app.UI.add_pm
    delete_button       = app.UI.delete_pm
    view_name           = 'f"{item.Name}"'
    tooltip             = 'f"Code:{item.Code} <br> {item.Quantity}"'
    search_bar          = app.UI.Pack_UI_SearchBar
    ui_list_info        = app.UI.PM_list_info
    dashboard           = app.UI.PM_DashBoard

    GRAPH_MODES = {
        'Inputs'    : show_inputs_graph,
        'Outputs'   : show_outputs_graph,
        'rework'    : show_reword_graph,
        'Ruin'      : show_ruins_graph,
    }

    last_year = datetime.date.today().replace(year = datetime.date.today().year - 1)
    next_year = datetime.date.today().replace(year = datetime.date.today().year + 1)

    PIE_GRAPH_MODES = {
        'rework_resions' : {
            'function': rework_resions_pie_data, 
            'extra_fields': {
                'From': Fields.DateField(default = last_year),
                'To': Fields.DateField(default = next_year)

            } 
        },
        'ruin_resions'      : {
            'function': ruin_resions_pie_data, 
            'extra_fields': {
                'From': Fields.DateField(default = last_year),
                'To': Fields.DateField(default = next_year)

            } 
        }
    }
    
    filters = {
        '#Low_Quantity_Materials:' : Low_Quantity_Materials_Filter,
        '#Quantity_Less_Than:' : Quantity_Less_Than,
        '#Quantity_More_Than:' : Quantity_More_Than,
        '#Low_Quantity_Warning_Active:' : Low_Quantity_Warning_Active
    }

    fields = {

        'Name'                     : Fields.CharField(),
        'Code'                     : Fields.CharField(),
        'Quantity'                 : Fields.FloatField(),
        'Low_Quantity_Warning'     : Fields.BoolField(),
        'Minimum_Quantity'         : Fields.FloatField(),
        'Materials_Inputs'         : Fields.ManyToManyField(subfields = {
            'Quantity'             : Fields.FloatField(),
            'Date_and_time'        : Fields.DateField(),
            'Note'                 : Fields.TextField()},
            view_name = '''f"""{ data['Quantity'] }  ({ data['Date_and_time'] }) """'''  ,
            tooltip   = '''f"""{ data['Note'] }  """'''  ,
            
        
        ),
        'Materials_Outputs'        : Fields.ManyToManyField(subfields = {

            'Quantity'             : Fields.FloatField(),
            'Date_and_time'        : Fields.DateField(),
            'Note'                 : Fields.TextField()},
            view_name = '''f"""{ data['Quantity'] }  ({ data['Date_and_time'] }) """'''  ,
            tooltip   = '''f"""{ data['Note'] }  """'''  ,
            
            ),
        
        'rework'        : Fields.ManyToManyField(subfields = {
            'Quantity'             : Fields.FloatField(),
            'Date_and_time'        : Fields.DateField(),
            'Reason'               : Fields.CustomListField(list_name = 'PM_REWORD_REASON'),
            'Quantity_Reword'      : Fields.BoolField(),
            'Note'                 : Fields.TextField()},
            view_name = '''f"""{ data['Quantity'] }  ({ data['Date_and_time'] }) """'''  ,
            tooltip   = '''f"""{ data['Reason'] }  """'''  ,
            
            ),
        'Ruin'        : Fields.ManyToManyField(subfields = {

            'Quantity'             : Fields.FloatField(),
            'Date_and_time'        : Fields.DateField(),
            'Reason'               : Fields.CustomListField(list_name = 'PM_RUIN_REASON'),
            'Quantity_Withdrawal'  : Fields.BoolField(),
            'Note'                 : Fields.TextField()},
            view_name = '''f"""{ data['Quantity'] }  ({ data['Date_and_time'] }) """'''  ,
            tooltip   = '''f"""{ data['Reason'] }  """'''  ,
            
            ),
        'extra_info'                        : Fields.ManyToManyField(subfields={
            'name'                          : Fields.CharField(),
            'value'                         : Fields.CharField(),
                },
            view_name = """ f'{data["name"]}:  {data["value"]}' """,
            ),
        'extra_records'            : Fields.ManyToManyField(subfields={
            'Record_Name'          : Fields.CharField(),
            'data'                 : Fields.ManyToManyField(subfields={
                'Title'            : Fields.CharField(),
                'Info'             : Fields.TextField()
                },
                view_name = """f'{data["Title"]}'""",
                single_view = True)
            },
            view_name = """f'{data["Record_Name"]}'"""
            )
            
            
            }
            

######################################################################################################
####################################Unpackged Product#################################################
######################################################################################################

class Mixed_Material(Model):
    #######################################################################
    ######################## SIGNALS ######################################
    #######################################################################
    filters={}



    ####################################################
    ###################Build############################
    ####################################################
    ui_list = app.UI.unpacked_product_list
    
    add_button          = app.UI.add_Mixed_Material
    delete_button       = app.UI.delete_Mixed_Material
    view_name           = 'f"{item.Name}"'
    tooltip             = 'f"Code:{item.Code}  "'
    search_bar          = app.UI.Mixed_Materials_UI_SearchBar
    ui_list_info        = app.UI.Mixed_Material_list_info

    def on_change_material(ui, field, ui_loaded = True):
        units = {'solid':['MG','CG','DG','G','DAG','HG','KG','T'],'liquid':['ML','CL','DL','L','DAL','HL','KL'],'gas':['ML','CL','DL','L','DAL','HL','KL']}
        current_material = ui.app.Raw_material.get(id = field.currentData())
        ui.unit.clear()
        for unit in units[current_material.Material_type]:
            ui.unit.addItem(unit)

    fields = {


        'Name'                     : Fields.CharField(),
        'Code'                     : Fields.CharField(),
        'Raw_materials'                       : Fields.ManyToManyField(subfields={
            'material'             : Fields.OneToOneField(model = 'Raw_material', on_change = on_change_material),
            'quantity'             : Fields.FloatField(),
            'unit'                 : Fields.ListField(),
            
            }, 
            view_name = """f'{data["material"]} {data["quantity"]} {data["unit"]}'""",
            single_view = True),
        'extra_info'                        : Fields.ManyToManyField(subfields={
            'name'                          : Fields.CharField(),
            'value'                         : Fields.CharField(),
            
            },
            view_name = """ f'{data["name"]}:  {data["value"]}' """,
            ),
        'extra_records'            : Fields.ManyToManyField(subfields={
            'Record_Name'          : Fields.CharField(),
            'data'                 : Fields.ManyToManyField(subfields={
                'Title'            : Fields.CharField(),
                'Info'             : Fields.TextField()
                },
                view_name = """f'{data["Title"]}'""",
                single_view = True)
            },
            view_name = """f'{data["Record_Name"]}'"""
            )
        }
        
######################################################################################################
####################################Final Product#################################################
######################################################################################################

class Final_product(Model):
    filters={}


    ####################################################
    ###################Build############################
    ####################################################
    ui_list             = app.UI.final_product_list
    add_button          = app.UI.add_final_product
    delete_button       = app.UI.delete_final_product
    view_name           = 'f"{item.Name}"'
    tooltip             = 'f"Code:{item.Code} "'
    search_bar          = app.UI.Final_products_UI_SearchBar
    ui_list_info        = app.UI.final_product_list_info
    
    
    fields = {


        'Name'                     : Fields.CharField(),
        'Code'                     : Fields.CharField(),
        'Mixed_Material'       : Fields.OneToOneField(model = 'Mixed_Material'),
        'Amount'                   : Fields.FloatField(),
        'packaging_materials'      : Fields.ManyToManyField(subfields={
            'material'             : Fields.OneToOneField(model = 'Packaging_Material'),
            'count'           : Fields.FloatField(),
            
            }, 
            view_name = """f'{data["material"]} {data["count"]}'""",
            single_view = True),
        'extra_info'                        : Fields.ManyToManyField(subfields={
            'name'                          : Fields.CharField(),
            'value'                         : Fields.CharField(),
            
            },
            view_name = """ f'{data["name"]}:  {data["value"]}' """,
            ),
        'extra_records'            : Fields.ManyToManyField(subfields={
            'Record_Name'          : Fields.CharField(),
            'data'                 : Fields.ManyToManyField(subfields={
                'Title'            : Fields.CharField(),
                'Info'             : Fields.TextField()
                },
                view_name = """f'{data["Title"]}'""",
                single_view = True)
            },
            view_name = """f'{data["Record_Name"]}'"""
            )
        }
        

class Final_Product_Plan(Model):

    def show_progress_graph(item):    
        return get_graph_data_type_2(item, item.Progress_data, info_form = '{} | {} '+ app.translate('Produced'), X_KEY = 'Date', Y_KEY = 'Actual_count')

    ####################################################
    ###################Build############################
    ####################################################
    
    def custom_str(self, item):
        if float(item.Count):
            perc = float(item.Completed) * 100 / float(item.Count)
            if perc == 100:
                perc = 'Completed!'
            else:
                perc = str(perc)+'%'
        else:
            perc = 'Empty'

        return f'{item.Name}    {perc}'

    ui_list = app.UI.final_products_plans_list
    
    add_button          = app.UI.add_FP_Plan
    delete_button       = app.UI.delete_FP_Plan
    view_name           = 'f"{item.Name}"'
    tooltip             = 'f"Code:{item.Code}"'
    dashboard           = app.UI.FPP_DashBoard
 

    fields = {

        'Name'                     : Fields.CharField(),
        'Code'                     : Fields.CharField(),
        'final_product'            : Fields.OneToOneField(model = 'Final_product'),
        'Count'                    : Fields.FloatField(),
        'Completed'                : Fields.FloatField(),
        'From_Date'                : Fields.DateField(),
        'To_Date'                  : Fields.DateField(),
        'Actual_To_Date'           : Fields.DateField(),
        'Note'                     : Fields.TextField(),
        'Progress'                 : Fields.ManyToManyField(subfields={
            'Expected_count'       : Fields.FloatField(),
            'Actual_count'         : Fields.FloatField(),
            'Date'                 : Fields.DateField(),
            'Shift'                : Fields.CustomListField(list_name = 'FP_plan_Progress_Shift'),
            'note'                 : Fields.TextField(),
            },
            view_name = '''f"""{ data['Actual_count'] } / { data['Expected_count'] } ({ data['Date'] }) """'''  ,
            tooltip   = '''f"""{ data['note'] }  """'''  ,
            single_view = True,
            ),
        'extra_info'                        : Fields.ManyToManyField(subfields={
            'name'                          : Fields.CharField(),
            'value'                         : Fields.CharField(),
                },
            view_name = """ f'{data["name"]}:  {data["value"]}' """,
            
            ),
        'extra_records'            : Fields.ManyToManyField(subfields={
            'Record_Name'          : Fields.CharField(),
            'data'                 : Fields.ManyToManyField(subfields={
                'Title'            : Fields.CharField(),
                'Info'             : Fields.TextField()
                },
                view_name = """f'{data["Title"]}'""",
                single_view = True)
            },
            view_name = """f'{data["Record_Name"]}'"""
            ),
        'pull_raw_materials'       : Fields.BoolField(default = False),
        'pull_packaging_materials' : Fields.BoolField(default = False)




    }

    GRAPH_MODES = {
        'Progress'    : show_progress_graph,

    }
    PIE_GRAPH_MODES = {
#        'rework_resions' : rework_resions_pie_data,
    }

    def before_add(self, item):
        item.check_amounts_status = self.check_amounts(self, item)
        return item.check_amounts_status

    def on_add(self, item):
        
        self.pull_amounts(self, item)

        
        if type(item.Progress) == str:
            item.Progress = json.loads(item.Progress.replace("'",'"'))
        added_progresses_value = sum([ i['Actual_count'] for i in item.Progress])
        item.Completed = added_progresses_value


        


    def before_edit(self, old_data, new_data):
        edited_item = self.get(id = old_data['id'])
        edited_item.Count -= old_data['Count']
        edited_item.check_amounts_status = self.check_amounts(self, edited_item)
        print(edited_item.check_amounts_status)
        
        edited_item.Count += old_data['Count']

        if edited_item.check_amounts_status: 
            if type(new_data['Progress']) == str:
                new_data['Progress'] = json.loads(new_data['Progress'].replace("'",'"'))

            if type(old_data['Progress']) == str:
                old_data['Progress'] = json.loads(old_data['Progress'].replace("'",'"'))

            added_amount = new_data['Count'] - old_data['Count']
            


            if type(edited_item.Progress) == str:
                edited_item.Progress = json.loads(edited_item.Progress.replace("'",'"'))
            added_progresses_value = sum([ i['Actual_count'] for i in edited_item.Progress])
            edited_item.Completed = added_progresses_value
            return True
        
        else:
            return False

    def on_edit(self, old_data, new_data):
        edited_item = self.get(id = old_data['id'])
        if edited_item.check_amounts_status:
            self.pull_amounts(self, edited_item, save=False)

    def check_amounts(self, model, item):
        enough_quantity = True
        final_product_count = float(item.Count)
        final_product_obj = model.INSApp.Final_product.get(id = int(item.final_product))
        if item.pull_raw_materials:
            for material in final_product_obj.packaging_materials:
                cu_material = model.INSApp.Packaging_Material.get(id = material['material'])
                if cu_material.Quantity < (material["count"]*final_product_count):
                    enough_quantity = False
                    #notifiers.Notification( model.INSApp.translate("Error")  ,model.INSApp.translate("You don't have enough quantity of {} material to add this order").format(cu_material.Name),model.INSApp.app_logo ).show()
                    break

        if enough_quantity and item.pull_packaging_materials:
            Mixed_Material_obj = final_product_obj.Mixed_Material__obj
            if Mixed_Material_obj != None:
                for material in Mixed_Material_obj.Raw_materials:
                    cu_material = model.INSApp.Raw_material.get(id = material['material'])
                    cu_material_base_quantity = Get_Base_Quantity(cu_material.Unit, cu_material.Quantity)
                    material_base_quantity = Get_Base_Quantity(material['unit'], material['quantity'])
                    if cu_material_base_quantity < (material_base_quantity*final_product_count * final_product_obj.Amount):
                        enough_quantity = False
                        #notifiers.Notification( model.INSApp.translate("Error")  ,model.INSApp.translate("You don't have enough quantity of {} material to add this order").format(cu_material.Name),model.INSApp.app_logo ).show()
            
        return enough_quantity
    
    def pull_amounts(self, model, item, save = True):
        final_product_count = float(item.Count)
        final_product_obj = model.INSApp.Final_product.get(id = int(item.final_product))
        if item.pull_raw_materials:
            for material in final_product_obj.packaging_materials:
                cu_material = model.INSApp.Packaging_Material.get(id = material['material'])
                cu_material.Quantity -= (material["count"]*final_product_count)
                cu_material.save()
                print('pulled rm', cu_material)

                    
        Mixed_Material_obj = final_product_obj.Mixed_Material__obj
        if item.pull_packaging_materials and  Mixed_Material_obj != None:
            for material in Mixed_Material_obj.Raw_materials:
                cu_material = model.INSApp.Raw_material.get(id = material['material'])
                cu_material_base_quantity = Get_Base_Quantity(cu_material.Unit, cu_material.Quantity)
                material_base_quantity = Get_Base_Quantity(material['unit'], material['quantity'])
                print(material_base_quantity,final_product_count, final_product_obj.Amount)
                cu_material_base_quantity -= (material_base_quantity*final_product_count* final_product_obj.Amount)
                cu_qu = get_perfect_unit(cu_material_base_quantity, cu_material.Material_type)
                cu_material.Quantity = cu_qu[0]
                cu_material.Unit = cu_qu[1]
                cu_material.save()
                print('pulled pm', cu_material, cu_qu)

    ####################################################
    ####################################################
    ####################################################






app.listed_items = [
    Repository,
    Raw_material,
    Mixed_Material,
    Packaging_Material,
    Final_product,
    Final_Product_Plan
    ]


def get_perfect_unit( quantity,m_type):
        m_type = m_type.upper()
        con_quantity = float(quantity)
        if m_type == 'SOLID':
            unit = 'G'
            cov_keys = ['MG','CG','DG','G','DAG','HG','KG','T']
            
        else:
            unit = 'L'
            cov_keys = ['ML','CL','DL','L','DAL','HL','KL']
         
        if con_quantity >= 10:
                while con_quantity >= 10:
                    current_unit_index = cov_keys.index(unit)
                    if current_unit_index +1 <  len(cov_keys):
                        con_quantity =  con_quantity /10
                        current_unit_index = cov_keys.index(unit)
                        new_unit_index = current_unit_index - 1
                        unit = cov_keys[new_unit_index]
                    else:
                        break

        
        elif con_quantity < 1:
                while con_quantity < 1:
                    current_unit_index = cov_keys.index(unit)
                    if current_unit_index +1 <  len(cov_keys):
                        con_quantity    *=10
                        new_unit_index  = current_unit_index - 1
                        unit            = cov_keys[new_unit_index]

                    else: 
                        break
        
        return [con_quantity, unit]


def get_graph_data_type_1(item, field, info_form):
        
        data = {}
        earliest_date = None
        latest_date = None

        smalles_value = 0
        biggest_value = 0

        x_data = []
        all_dates = []

        sorted_points = {}
        point_data = {}

        if len(field):
            for m_input in field:
                value = Get_Base_Quantity( m_input['Unit'], m_input['Quantity'])

                if m_input['Date_and_time'] in data.keys():
                    data[m_input['Date_and_time']] += value

                else:
                    data[m_input['Date_and_time']] = value

            y_data = list(data.values())
            biggest_value = max(list(data.values()))
            smalles_value = min(list(data.values()))



            for date_data in data:
                if latest_date == None:
                    latest_date = datetime.date.fromisoformat(date_data)
                
                elif latest_date < datetime.date.fromisoformat(date_data):
                    latest_date = datetime.date.fromisoformat(date_data)

                if earliest_date == None:
                    earliest_date = datetime.date.fromisoformat(date_data)
                
                elif earliest_date > datetime.date.fromisoformat(date_data):
                    earliest_date = datetime.date.fromisoformat(date_data)
            
            delta = latest_date - earliest_date       # as timedelta

            
            for i in range(delta.days + 1):
                day = earliest_date + datetime.timedelta(days=i)
                all_dates.append(day.isoformat())
            x_data = [ all_dates.index(i) for i in data.keys() ]

            #all_values = range(int(smalles_value), int(biggest_value)+1)


            points = { x_data[i]:y_data[i] for i in range(len(x_data)) }
            sorted_x = sorted(points)
            for point in sorted_x:
                sorted_points[point] = points[point]
                quantity = get_perfect_unit(points[point],item.Material_type)
                quantity = f'{str(quantity[0])} {quantity[1]}'
                point_data[point] = info_form.format(all_dates[point],  quantity) 

        if smalles_value < 0:
            y_range = biggest_value - smalles_value
        else:
            y_range = biggest_value

            
        g_values = {
            'x-keys' : ['.']*len(all_dates),
            'y-keys' : [str(i) for i in range( int(y_range)+2 )],
                              
            'x' : list(sorted_points.keys()),
            'y' : list(sorted_points.values()),

            'point-data':point_data,
        }
        return g_values




def get_graph_data_type_2(item, field, info_form, Y_KEY = 'Quantity', X_KEY = 'Date_and_time' ):
        
        data = {}
        earliest_date = None
        latest_date = None

        smalles_value = 0
        biggest_value = 0

        x_data = []
        all_dates = []

        sorted_points = {}
        point_data = {}

        if len(field):
            for m_input in field:
                value = m_input[Y_KEY]

                if m_input[X_KEY] in data.keys():
                    data[m_input[X_KEY]] += value

                else:
                    data[m_input[X_KEY]] = value

            y_data = list(data.values())
            biggest_value = max(list(data.values()))
            smalles_value = min(list(data.values()))



            for date_data in data:
                if latest_date == None:
                    latest_date = datetime.date.fromisoformat(date_data)
                
                elif latest_date < datetime.date.fromisoformat(date_data):
                    latest_date = datetime.date.fromisoformat(date_data)

                if earliest_date == None:
                    earliest_date = datetime.date.fromisoformat(date_data)
                
                elif earliest_date > datetime.date.fromisoformat(date_data):
                    earliest_date = datetime.date.fromisoformat(date_data)
            
            delta = latest_date - earliest_date       # as timedelta

            
            for i in range(delta.days + 1):
                day = earliest_date + datetime.timedelta(days=i)
                all_dates.append(day.isoformat())
            x_data = [ all_dates.index(i) for i in data.keys() ]

            #all_values = range(int(smalles_value), int(biggest_value)+1)


            points = { x_data[i]:y_data[i] for i in range(len(x_data)) }
            sorted_x = sorted(points)
            for point in sorted_x:
                sorted_points[point] = points[point]
                quantity = str(points[point])
                point_data[point] = info_form.format(all_dates[point],  quantity) 

        if smalles_value < 0:
            y_range = biggest_value - smalles_value
        else:
            y_range = biggest_value

            
        g_values = {
            'x-keys' : ['.']*len(all_dates),
            'y-keys' : [str(i) for i in range( int(y_range)+2 )],
                              
            'x' : list(sorted_points.keys()),
            'y' : list(sorted_points.values()),

            'point-data':point_data,
        }
        return g_values




def Get_Base_Quantity( unit, quantity):
        quantity = float(quantity)
        cov = { 'MG': 1000,'CG':100,'DG':10,'G':1,
                'DAG': 0.1,'HG':0.01,'KG':0.001,'T':0.0001,
                
                'ML': 1000,'CL':100,'DL':10,'L':1,
                'DAL': 0.1,'HL':0.01,'KL':0.001,'T':0.0001}
        quantity /= cov[unit.upper()]
        return quantity

def Get_Quantity_for_Static_Unit(  unit, quantity):
        quantity = float(quantity)
        cov = { 'MG': 1000,'CG':100,'DG':10,'G':1,
                'DAG': 0.1,'HG':0.01,'KG':0.001,'T':0.0001,
                
                'ML': 1000,'CL':100,'DL':10,'L':1,
                'DAL': 0.1,'HL':0.01,'KL':0.001,'T':0.0001}
        quantity *= cov[unit.upper()]
        return quantity


app.run()

