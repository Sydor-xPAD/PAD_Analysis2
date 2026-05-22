#!/usr/bin/env python3
# File: UI_utils.py
# Description - 
#
# History
# v 0.1 8/5/23 YF - Inception
import tkinter as tk
import tkinter.ttk as ttk
import json

class UIPage:
    def __init__(self, tup_Name_Descrip):
        # assert somehow that tup_Name_Descrip is list of string pairs
        self.tup_Name_Descrip = tup_Name_Descrip
        self.selectedActions = () # empty tuple
        self.cancelled = False

          # Load previous selections from the configuration file
        self.selections = self.load_selections()

        self.root = tk.Tk()
        self.root.title("Choose action")
        # Bind the close event to the on_closing function
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Create a variable to hold the checkbox state
        
        
        d = self.selections
        
        self.cb_TakeData = tk.BooleanVar(value= d.get("cb0", False) )
        self.cb_AnalyzeData = tk.BooleanVar( value = d.get("cb1", False) )  

        self.lb_ScriptToRun = tk.Listbox( self.root, width=30 )

        # Create a label to display the selection
        self.selection_label = tk.Label(self.root, text="<Description>", wraplength=200)
         # Create a label to display the result
        self.result_label = ttk.Label(self.root, text="")
        self.cancelButton = tk.Button(self.root, text="Cancel", 
            command=self.btnCancel_click)
        
        self.OKButton = tk.Button(self.root, text="OK",  width=10, background='#108810',
            command=self.btnOK_click)
        

        self.buildList()
            
        self.lb_ScriptToRun.select_clear(0, tk.END)
        n = d.get("lb1")
        self.lb_ScriptToRun.selection_set(n if n else 0 )
     
        self.checkboxes = [ self.cb_TakeData, self.cb_AnalyzeData]
        self.on_select(None)
        
       

    def on_closing(self):
        self.saveOptions()
        self.selectedActions = self.cb_TakeData.get(), self.cb_AnalyzeData.get()
        self.root.destroy()



    def btnCancel_click(self):
        self.cancelled = True
        self.root.destroy()

    def btnOK_click(self):
        self.on_closing()

    def buildList(self):
        lb = self.lb_ScriptToRun
        n=0
        # Populate the listbox
        for (s,d) in self.tup_Name_Descrip:
            lb.insert(n,s)
            n += 1
       
        lb.bind("<<ListboxSelect>>", self.on_select)

    def cb_clicked(self):
        """
        checkbox handler
        """

        txtA = ""
        txtB = ""

        if self.cb_TakeData.get():
            txtA= "TakeData"

        if self.cb_AnalyzeData.get():
            txtB ="Analyze"
            
        
        if txtA and txtB:
            txtA = txtA + " & "

        self.result_label.config(text=f"{txtA} {txtB}")
       
                                 

    def on_select(self,event):
        """
        listbox handler
        """

        lb = self.lb_ScriptToRun
        lbl = self.selection_label
        n = lb.curselection()
        if len(n):
           descrip_text = self.tup_Name_Descrip[n[0]][1]
           lbl.config(text=f"Description: {descrip_text}")
           self.selectedText = self.tup_Name_Descrip[ n[0] ][0]
    
    def show(self):
        # Create the main window
        
        # unpack to allow less typing
        td = self.cb_TakeData
        ad = self.cb_AnalyzeData
        root = self.root
        lb = self.lb_ScriptToRun

        r = 0

        # Create a checkbox
        checkbox1 = ttk.Checkbutton(root, 
            text="Take Data", variable=td, command=self.cb_clicked, padding=(5,5) )
        checkbox2 = ttk.Checkbutton(root, 
            text="Analyze Data", variable=ad, command=self.cb_clicked, padding = (5,5))
        
       # Grid layout for checkboxes
        checkbox1.grid(row=r, column=0)
        checkbox2.grid(row=r, column=1)
        r += 1
                
        # Create a label 
        lbl1 = tk.Label(root, text="Choose what to run:")
        lbl1.grid(row=r); r += 1


        lb.grid(row=r, column=0, columnspan=2, padx=20); r += 1        
        self.selection_label.grid(row=r, columnspan=2); r += 1       
        self.result_label.grid(row=r, columnspan=2); r +=1
        self.cancelButton.grid(row=r, column=0);
        self.OKButton.grid(row=r, column=1);   r +=1

        # Create an empty label to add space under the button
        #empty_label = tk.Label(root, text="", height=1)  # Adjust the height as needed
        #empty_label.grid(row=r, column=0); r += 1

        root.grid_rowconfigure( r-1, minsize=40)  # Adjust minsize as needed

        # Start the GUI event loop
        root.mainloop()



    def load_selections(self):
        try:
            with open("config.json", "r") as config_file:
                return json.load(config_file)
        except (FileNotFoundError, json.JSONDecodeError):
            return {} 
        

    def saveOptions(self):
        self.selections = {f"cb{idx}": checkbox_var.get() for idx, checkbox_var in enumerate(self.checkboxes)}
        self.selections["lb1"] = self.lb_ScriptToRun.curselection()[0]

        with open("config.json", "w") as config_file:
            json.dump(self.selections, config_file)



# Entry point of the script
if __name__ == "__main__":
    lot = []
    lot.append( ("ABC", "A very very long and windy description for ABC"))
    lot.append( ("DEF", "Descrip _ DEF" ))
    
    ui = UIPage( lot )
    ui.show()
    
