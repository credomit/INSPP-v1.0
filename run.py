from INSLPCModel.fields import Fields
from INSLPCModel.Model import INSAPP, Model
from INSLPCModel.Statements import *
import json, notify2, random
import datetime

btn_list = []#'TR_LABEL', 'DELETE_BUTTON_2','ADD_BUTTON_2','DELETE_BUTTON','ADD_BUTTON','ADD_LANGUAGE_BTN']


app = INSAPP(
    app_name= 'inspp',
    app_file_type = 'inspp',
    app_logo = 'main.png',
    translateable_labels_and_buttons = btn_list,

    )


def Get_Base_Quantity( unit, quantity):
        quantity = float(quantity)
        cov = { 'MG': 1000,'CG':100,'DG':10,'G':1,
                'DAG': 0.1,'HG':0.01,'KG':0.001,'T':0.0001,
                
                'ML': 1000,'CL':100,'DL':10,'L':1,
                'DAL': 0.1,'HL':0.01,'KL':0.001,'T':0.0001}
        quantity /= cov[unit.upper()]
        return quantity

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
                    print(obj_base_quantity , value_base_quantity)
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
                    print(obj_base_quantity , value_base_quantity)
                    if obj_base_quantity > value_base_quantity : 
                        QMT_list.append(obj)
            except:
                pass
        return QMT_list


    def Low_Quantity_Warning_Active(self, objects, **kwagrs):
        print('fff4')
        LQWA_list = []
        for obj in objects:
            if obj.Low_Quantity_Warning:
                LQWA_list.append(obj)

        return LQWA_list

    #######################################################################
    ######################## SIGNALS ######################################
    #######################################################################

    def on_edit(self, old_data, new_data):
        edited_item = self.get(id = old_data['id'])
        
        old_inputs      = json.loads(old_data['Materials_Inputs'])
        old_outputs     = json.loads(old_data['Materials_Outputs'])
        old_reword      = json.loads(old_data['Reword'])
        old_ruin        = json.loads(old_data['Ruin'])

        

        new_inputs      = json.loads(new_data['Materials_Inputs'])
        new_outputs     = json.loads(new_data['Materials_Outputs'])
        new_reword      = json.loads(new_data['Reword'])
        new_ruin        = json.loads(new_data['Ruin'])

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
                notify2.Notification( self.INSApp.translate("Warning")  ,self.INSApp.translate("You have low quantity of") + str(edited_item) ,self.INSApp.app_logo ).show()


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
        if type(item.Reword) == str:
            item.Reword = json.loads(item.Reword)
        return get_graph_data_type_1(item, item.Reword, info_form = '{} | {} '+ app.translate('Used') )


    def show_ruins_graph(item):
        if type(item.Ruin) == str:
            item.Ruin = json.loads(item.Ruin)
        return get_graph_data_type_1(item, item.Ruin, info_form = '{} | {} '+ app.translate('Used') )
    #######################################################################
    ######################## BUILD ########################################
    #######################################################################




    ui_list = app.UI.RawMaterials_UI_List
    
    add_button          = app.UI.RawMaterial_Add_Button
    delete_button       = app.UI.RawMaterial_Edit_Button
    view_name           = 'f"{item.Name}"'
    tooltip             = 'f"Code:{item.Code} <br> {item.Quantity} {item.Unit} "'
    search_bar          = app.UI.RawMaterials_UI_SearchBar
    ui_list_info        = app.UI.raw_materials_list_info
    dashboard           = app.UI.RM_DashBoard

    GRAPH_MODES = {
        'Inputs'    : show_inputs_graph,
        'Outputs'   : show_outputs_graph,
        'Reword'    : show_reword_graph,
        'Ruin'      : show_ruins_graph,
    }
    

    filters = {
        '#Low Quantity Materials' : Low_Quantity_Materials_Filter,
        '#Quantity Less Than:' : Quantity_Less_Than,
        '#Quantity More Than:' : Quantity_More_Than,
        '#Low Quantity Warning Active' : Low_Quantity_Warning_Active,
    }

    fields = {

        'Name'                     : Fields.CharField(),
        'Code'                     : Fields.CharField(),
        'Material_type'            : Fields.DictField(item_dict = {'solid':['MG','CG','DG','G','DAG','HG','KG','T'],'liquid':['ML','CL','DL','L','DAL','HL','KL'],'gas':['ML','CL','DL','L','DAL','HL','KL']} , subfields = ['Unit','Minimum_Unit']),
        'Quantity'                 : Fields.FloatField(),
        'Unit'                     : Fields.ListField(),
        'Low_Quantity_Warning'     : Fields.BoolField(),
        'Minimum_Quantity'         : Fields.FloatField(),
        'Minimum_Unit'             : Fields.ListField(),
        'Materials_Inputs'         : Fields.ManyToManyField(subfields = {
            'Quantity'             : Fields.FloatField(),
            'Unit'                 : Fields.ListField(data_from_DictField =  'Material_type'),
            'Date_and_time'        : Fields.DateField(),
            'Note'                 : Fields.TextField()},
            view_name = '''f"""{ data['Quantity'] } { data['Unit'] } ({ data['Date_and_time'] }) """'''  ,
            tooltip   = '''f"""{ data['Note'] }  """'''  ,
            
        
        ),
        'Materials_Outputs'        : Fields.ManyToManyField(subfields = {

            'Quantity'             : Fields.FloatField(),
            'Unit'                 : Fields.ListField(data_from_DictField =  'Material_type'),
            'Date_and_time'        : Fields.DateField(),
            'Note'                 : Fields.TextField()},
            view_name = '''f"""{ data['Quantity'] } { data['Unit'] } ({ data['Date_and_time'] }) """'''  ,
            tooltip   = '''f"""{ data['Note'] }  """'''  ,
            
            ),
        
        'Reword'        : Fields.ManyToManyField(subfields = {

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
        old_reword      = json.loads(old_data['Reword'])
        old_ruin        = json.loads(old_data['Ruin'])

        new_inputs      = json.loads(new_data['Materials_Inputs'])
        new_outputs     = json.loads(new_data['Materials_Outputs'])
        new_reword      = json.loads(new_data['Reword'])
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
                notify2.Notification( self.INSApp.translate("Warning")  ,self.INSApp.translate("You have low quantity of") + str(edited_item) ,self.INSApp.app_logo ).show()

    #######################################################################
    ######################## FILTERS ######################################
    #######################################################################

    def Low_Quantity_Materials_Filter(self, objects, **kwagrs):
        print('d')
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
                print(quantity)
                for obj in objects:
                    print('vv', obj.Quantity)
                    obj_quantity = obj.Quantity
                    print(obj_quantity < quantity, obj_quantity , quantity)
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
        print('d')
        for obj in objects:
            if obj.Low_Quantity_Warning:
                LQWA_list.append(obj)

        return LQWA_list

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
        
        'Reword'        : Fields.ManyToManyField(subfields = {
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

class Unpackaged_product(Model):
    #######################################################################
    ######################## SIGNALS ######################################
    #######################################################################
    filters={}
    def before_add(data):
        temp = []
        sum1 = 0

        for i in data['item_object'].Raw_materials_data:
            temp.append(i["Percentage"])
            sum1 = sum(temp)

        if sum1 + float(data["Percentage"]) <= 100:
            return True
        else:
            notify2.Notification( data['item_object'].model.INSApp.translate("Warning")  ,data['item_object'].model.INSApp.translate("The Percentage Is More Than 100") ,data['item_object'].model.INSApp.app_logo ).show()
            return False

    ####################################################
    ###################Build############################
    ####################################################
    ui_list = app.UI.unpacked_product_list
    
    add_button          = app.UI.add_unpackaged_product
    delete_button       = app.UI.delete_unpackaged_product
    view_name           = 'f"{item.Name}"'
    tooltip             = 'f"Code:{item.Code}  "'
    search_bar          = app.UI.Unpackaged_products_UI_SearchBar
    ui_list_info        = app.UI.Unpackaged_product_list_info

    fields = {


        'Name'                     : Fields.CharField(),
        'Code'                     : Fields.CharField(),
        'Raw_materials'                       : Fields.ManyToManyField(subfields={
            'material'             : Fields.OneToOneField(model = 'Raw_material'),
            'Percentage'           : Fields.FloatField(),
            
            }, 
            view_name = """f'{data["material"]} {data["Percentage"]}%'""",
            before_add = before_add,
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
        'Unpackaged_product'       : Fields.OneToOneField(model = 'Unpackaged_product'),
        ''
        'packaging_materials'                       : Fields.ManyToManyField(subfields={
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
        

class Order(Model):
    ####################################################
    ###################Build############################
    ####################################################
    ui_list = app.UI.orders_list
    
    add_button          = app.UI.add_order
    delete_button       = app.UI.delete_order
    edit_button         = app.UI.edit_order
    view_name           = 'f"{item.Name}"'
    tooltip             = 'f"Code:{item.Code}"'

    fields = {

        'Name'                     : Fields.CharField(),
        'Code'                     : Fields.CharField(),
        'packed_product'           : Fields.OneToOneField(model = 'packaged_product'),
        'Quantity'                 : Fields.FloatField(),
        'From_Date'                : Fields.DateField(),
        'To_Date'                  : Fields.DateField(),
        'Actual_To_Date'           : Fields.DateField(),
        'Note'                     : Fields.TextField(),
        'Done'                     : Fields.BoolField(),
        'Progress'                 : Fields.ManyToManyField(subfields={
            'Expected_Percentage'  : Fields.FloatField(),
            'Percentage'           : Fields.FloatField(),
            'Shift'                : Fields.CustomListField(list_name = 'Order_Progress_Shift')
            }),

        'Reword'        : Fields.ManyToManyField(subfields = {
            'Quantity'             : Fields.FloatField(),
            'Unit'                 : Fields.ListField(data_from_DictField =  ''),
            'Date_and_time'        : Fields.DateField(),
            'Reason'               : Fields.CustomListField(list_name = 'PM_REWORD_REASON'),
            'Note'                 : Fields.TextField()},
            view_name = '''f"""{ data['Quantity'] } { data['Unit'] } ({ data['Date_and_time'] }) """'''  ,
            tooltip   = '''f"""{ data['Reason'] }  """'''  ,
            ),

        'Ruin'        : Fields.ManyToManyField(subfields = {

            'Quantity'             : Fields.FloatField(),
            'Unit'                 : Fields.ListField(data_from_DictField =  ''),
            'Reason'               : Fields.CustomListField(list_name = 'PM_RUIN_REASON'),
            'Date_and_time'        : Fields.DateField(),
            'Note'                 : Fields.TextField()},
            view_name = '''f"""{ data['Quantity'] } { data['Unit'] } ({ data['Date_and_time'] }) """'''  ,
            tooltip   = '''f"""{ data['Reason'] }  """'''  ,
            
            )

             }

    ####################################################
    ####################################################
    ####################################################






app.listed_items = [
    Raw_material,
    Unpackaged_product,
    Packaging_Material,
    Final_product,
    #Order
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
                    #print('1', con_quantity)
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
                        new_unit_index  = current_unit_index + 1
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




app.run()

