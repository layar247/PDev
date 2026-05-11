import tkinter as tk
from tkinter import ttk, messagebox
from db import fetch_all, execute_query
from forms.order_form import OrderForm
from forms.payment_form import PaymentForm
from forms.add_supplier_form import AddSupplierForm
from forms.reference_form import ReferenceForm
from utils.excel_report import generate_report_for_supplier

class MainForm(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Заказы поставщиков")
        self.geometry("800x500")
        self.create_widgets()
        self.load_orders()

    def create_widgets(self):
        # Таблица заказов
        self.tree = ttk.Treeview(self, columns=('order_id', 'supplier', 'order_date', 'delivery_date', 'status', 'total_amount'), show='headings')
        self.tree.heading('order_id', text='ID')
        self.tree.heading('supplier', text='Поставщик')
        self.tree.heading('order_date', text='Дата заказа')
        self.tree.heading('delivery_date', text='Дата доставки')
        self.tree.heading('status', text='Статус')
        self.tree.heading('total_amount', text='Сумма')
        self.tree.column('order_id', width=0, stretch=False)  # скрываем ID
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Button(btn_frame, text="Новый заказ", command=self.new_order).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Обновить", command=self.load_orders).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Оплатить", command=self.pay_order).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Удалить", command=self.delete_order).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Отменить заказ", command=self.cancel_order).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Сформировать отчёт", command=self.generate_report).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Справочник товаров", command=self.open_reference).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Добавить поставщика", command=self.add_supplier).pack(side=tk.LEFT, padx=5)

    def load_orders(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        rows = fetch_all("""
            SELECT o.order_id, s.name as supplier, o.order_date, o.delivery_date, o.status, o.total_amount
            FROM orders o JOIN suppliers s ON o.supplier_id = s.supplier_id
            ORDER BY o.order_date DESC
        """)
        for r in rows:
            self.tree.insert('', tk.END, values=(r['order_id'], r['supplier'], r['order_date'], r['delivery_date'], r['status'], r['total_amount']))

    def get_selected_order_id(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите заказ")
            return None
        return self.tree.item(selected[0])['values'][0]

    def new_order(self):
        OrderForm(self)

    def pay_order(self):
        order_id = self.get_selected_order_id()
        if order_id:
            PaymentForm(self, order_id)

    def delete_order(self):
        order_id = self.get_selected_order_id()
        if not order_id:
            return
        if messagebox.askyesno("Удаление", "Удалить выбранный заказ?"):
            execute_query("DELETE FROM orders WHERE order_id = %s", (order_id,))
            self.load_orders()

    def cancel_order(self):
        order_id = self.get_selected_order_id()
        if not order_id:
            return
        if messagebox.askyesno("Отмена", "Отменить выбранный заказ?"):
            execute_query("UPDATE orders SET status = 'Отменен' WHERE order_id = %s", (order_id,))
            self.load_orders()

    def generate_report(self):
        order_id = self.get_selected_order_id()
        if order_id:
            generate_report_for_supplier(order_id)

    def open_reference(self):
        ReferenceForm(self)

    def add_supplier(self):
        AddSupplierForm(self)
