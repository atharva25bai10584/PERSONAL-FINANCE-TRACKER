

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json, os, csv
from datetime import datetime
from collections import defaultdict
from decimal import Decimal, InvalidOperation

class DataStorage:
    def __init__(self, file="finance_data.json"):
        self.file = file
        self.data = {"transactions": [], "categories": ["Salary","Food","Transport","Bills","Shopping","Misc"]}
        self.load()

    def load(self):
        if os.path.exists(self.file):
            try:
                with open(self.file,"r",encoding="utf-8") as f:
                    self.data.update(json.load(f))
            except: self.save()
        else: self.save()

    def save(self):
        with open(self.file,"w",encoding="utf-8") as f:
            json.dump(self.data,f,indent=2)

    def add_transaction(self, t):
        self.data["transactions"].append(t)
        self.save()

    def delete_transaction(self, tid):
        before = len(self.data["transactions"])
        self.data["transactions"] = [x for x in self.data["transactions"] if x["id"] != tid]
        if len(self.data["transactions"]) < before:
            self.save()
            return True
        return False

    def update_transaction(self, tid, fields):
        for t in self.data["transactions"]:
            if t["id"] == tid:
                t.update(fields); self.save(); return True
        return False

    def list_transactions(self):
        return sorted(self.data["transactions"], key=lambda x: x["date"], reverse=True)

    def add_category(self,c):
        if c not in self.data["categories"]:
            self.data["categories"].append(c); self.save(); return True
        return False

    def export_csv(self, path):
        try:
            with open(path,'w',newline='',encoding='utf-8') as f:
                w=csv.DictWriter(f,fieldnames=["id","date","type","amount","category","desc"])
                w.writeheader(); w.writerows(self.data["transactions"])
            return True
        except Exception as e: return False

    def import_csv(self, path):
        try:
            with open(path,'r',encoding='utf-8') as f:
                r=csv.DictReader(f)
                for row in r:
                    row["id"]=int(datetime.utcnow().timestamp()*1000)
                    self.data["transactions"].append(row)
            self.save(); return True
        except: return False


class Reports:
    @staticmethod
    def monthly(trans):
        result = defaultdict(lambda: {"Income":Decimal("0"),"Expense":Decimal("0")})
        for t in trans:
            key=t["date"][:7]
            val=Decimal(t["amount"])
            result[key][t["type"]]+=val
        return result

    @staticmethod
    def categories(trans):
        res=defaultdict(Decimal)
        for t in trans:
            if t["type"]=="Expense": res[t["category"]]+=Decimal(t["amount"])
        return res


class App:
    def __init__(self,root):
        self.root=root; root.title("Personal Finance Tracker")
        self.db=DataStorage(); self.selected_id=None

        self.build_form()
        self.build_table()
        self.build_reports()

        self.refresh()

    def build_form(self):
        f=ttk.LabelFrame(self.root,text="Transaction")
        f.grid(row=0,column=0,sticky="nsew",padx=6,pady=6)

        self.date=tk.StringVar(); self.type=tk.StringVar(value="Expense")
        self.amount=tk.StringVar(); self.cat=tk.StringVar()
        self.desc=tk.StringVar()

        ttk.Label(f,text="Date YYYY-MM-DD").grid(row=0,column=0,sticky='w')
        ttk.Entry(f,textvariable=self.date).grid(row=0,column=1,sticky='ew')
        ttk.Label(f,text="Type").grid(row=1,column=0,sticky='w')
        ttk.Combobox(f,textvariable=self.type,values=["Expense","Income"],width=10).grid(row=1,column=1,sticky='ew')
        ttk.Label(f,text="Amount").grid(row=2,column=0,sticky='w')
        ttk.Entry(f,textvariable=self.amount).grid(row=2,column=1,sticky='ew')
        ttk.Label(f,text="Category").grid(row=3,column=0,sticky='w')
        self.catbox=ttk.Combobox(f,textvariable=self.cat,values=self.db.data["categories"])
        self.catbox.grid(row=3,column=1,sticky='ew')
        ttk.Label(f,text="Description").grid(row=4,column=0,sticky='w')
        ttk.Entry(f,textvariable=self.desc).grid(row=4,column=1,sticky='ew')

        btns=ttk.Frame(f); btns.grid(row=5,column=0,columnspan=2,pady=4)
        ttk.Button(btns,text="Add",command=self.add).grid(row=0,column=0,padx=2)
        ttk.Button(btns,text="Update",command=self.update).grid(row=0,column=1,padx=2)
        ttk.Button(btns,text="Delete",command=self.delete).grid(row=0,column=2,padx=2)
        ttk.Button(btns,text="Clear",command=self.clear).grid(row=0,column=3,padx=2)

        catf=ttk.Frame(f); catf.grid(row=6,column=0,columnspan=2,pady=4)
        self.newcat=tk.StringVar()
        ttk.Entry(catf,textvariable=self.newcat,width=12).grid(row=0,column=0)
        ttk.Button(catf,text="Add Category",command=self.add_cat).grid(row=0,column=1)

    def build_table(self):
        f=ttk.LabelFrame(self.root,text="Transactions")
        f.grid(row=0,column=1,sticky="nsew",padx=6,pady=6)
        cols=("date","type","amount","category","desc")
        self.table=ttk.Treeview(f,columns=cols,show="headings",height=15)
        for c in cols: self.table.heading(c,text=c.title())
        self.table.grid(row=0,column=0,sticky="nsew")
        self.table.bind("<<TreeviewSelect>>",self.select)

        s=ttk.Scrollbar(f,orient="vertical",command=self.table.yview)
        s.grid(row=0,column=1,sticky="ns"); self.table.configure(yscroll=s.set)

        optf=ttk.Frame(f); optf.grid(row=1,column=0,pady=4)
        ttk.Button(optf,text="Export CSV",command=self.export_csv).grid(row=0,column=0,padx=4)
        ttk.Button(optf,text="Import CSV",command=self.import_csv).grid(row=0,column=1,padx=4)

    def build_reports(self):
        f=ttk.LabelFrame(self.root,text="Reports")
        f.grid(row=1,column=0,columnspan=2,sticky="nsew",padx=6,pady=6)
        ttk.Button(f,text="Monthly Summary",command=self.show_monthly).grid(row=0,column=0,padx=5)
        ttk.Button(f,text="Category Summary",command=self.show_categories).grid(row=0,column=1,padx=5)
        self.txt=tk.Text(f,height=10); self.txt.grid(row=1,column=0,columnspan=2,sticky='nsew')

    def add(self):
        try:
            amt=Decimal(self.amount.get())
            d=self.date.get().strip() or datetime.utcnow().isoformat()[:10]
            tid=int(datetime.utcnow().timestamp()*1000)
            row={"id":tid,"date":d,"type":self.type.get(),"amount":str(amt),
                 "category":self.cat.get() or "Misc","desc":self.desc.get()}
            self.db.add_transaction(row); self.refresh(); self.clear()
        except InvalidOperation:
            messagebox.showerror("Error","Invalid amount")

    def update(self):
        if not self.selected_id: return
        try:
            self.db.update_transaction(self.selected_id,{
                "date":self.date.get(),
                "type":self.type.get(),
                "amount":self.amount.get(),
                "category":self.cat.get(),
                "desc":self.desc.get()
            }); self.refresh(); self.clear()
        except: pass

    def delete(self):
        if self.selected_id and self.db.delete_transaction(self.selected_id):
            self.refresh(); self.clear()

    def refresh(self):
        for i in self.table.get_children(): self.table.delete(i)
        for t in self.db.list_transactions():
            self.table.insert('',"end",values=(t["date"],t["type"],t["amount"],t["category"],t["desc"]),tags=(t["id"],))

    def select(self,e):
        sel=self.table.selection()
        if not sel: return
        vals=self.table.item(sel[0])["values"]
        self.selected_id=int(self.table.item(sel[0])["tags"][0])
        self.date.set(vals[0]); self.type.set(vals[1]); self.amount.set(vals[2])
        self.cat.set(vals[3]); self.desc.set(vals[4])

    def clear(self):
        self.date.set(""); self.amount.set(""); self.type.set("Expense")
        self.cat.set(""); self.desc.set(""); self.selected_id=None

    def add_cat(self):
        if self.db.add_category(self.newcat.get().strip()):
            self.catbox["values"]=self.db.data["categories"]

    def export_csv(self):
        path=filedialog.asksaveasfilename(defaultextension='.csv')
        if path and self.db.export_csv(path): messagebox.showinfo("Export","Done")

    def import_csv(self):
        path=filedialog.askopenfilename()
        if path and self.db.import_csv(path): self.refresh()

    def show_monthly(self):
        rep=Reports.monthly(self.db.list_transactions())
        self.txt.delete("1.0","end")
        for k,v in sorted(rep.items(),reverse=True):
            self.txt.insert("end",f"{k}  Income:{v['Income']}  Expense:{v['Expense']}  Net:{v['Income']-v['Expense']}\n")

    def show_categories(self):
        rep=Reports.categories(self.db.list_transactions())
        self.txt.delete("1.0","end")
        for c,v in rep.items():
            self.txt.insert("end",f"{c}: {v}\n")

if __name__=="__main__":
    r=tk.Tk(); r.minsize(900,500)
    App(r); r.mainloop()
