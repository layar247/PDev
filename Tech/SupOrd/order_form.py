import tkinter as tk
from tkinter import ttk, messagebox
from db import fetch_all, execute_query

class OrderForm(tk.Toplevel):
    def __init__(self, parent, order_id=None):
        super().__init__(parent)
        self.parent = parent
        self.order_id = order_id
        self.title("Редактирование заказа" if order_id else "Новый заказ")
        self.geometry("600x500")
        self.order_items = []  # список словарей {product_id, product, quantity, unit_price, amount}
        self.create_widgets()
        self.load_suppliers_products()
        if order_id:
            self.load_order_data()

    def create_widgets(self):
        tk.Label(self, text="Поставщик:").grid(row=0, column=0, sticky='e', padx=5, pady=2)
        self.supplier_cb = ttk.Combobox(self, state='readonly')
        self.supplier_cb.grid(row=0, column=1, sticky='ew', padx=5, pady=2)

        tk.Label(self, text="Дата заказа:").grid(row=1, column=0, sticky='e', padx=5, pady=2)
        self.order_date = tk.Entry(self)
        self.order_date.grid(row=1, column=1, sticky='ew', padx=5, pady=2)

        tk.Label(self, text="Дата доставки:").grid(row=2, column=0, sticky='e', padx=5, pady=2)
        self.delivery_date = tk.Entry(self)
        self.delivery_date.grid(row=2, column=1, sticky='ew', padx=5, pady=2)

        tk.Label(self, text="Статус:").grid(row=3, column=0, sticky='e', padx=5, pady=2)
        self.status_cb = ttk.Combobox(self, values=['Новый', 'В обработке', 'Отменен', 'Оплачен'], state='readonly')
        self.status_cb.grid(row=3, column=1, sticky='ew', padx=5, pady=2)
        self.status_cb.current(0)

        tk.Label(self, text="Товары:").grid(row=4, column=0, sticky='ne', padx=5, pady=2)
        frame_items = tk.Frame(self)
        frame_items.grid(row=4, column=1, columnspan=2, sticky='nsew', padx=5, pady=2)

        self.items_tree = ttk.Treeview(frame_items, columns=('product', 'quantity', 'unit_price', 'amount'), show='headings')
        self.items_tree.heading('product', text='Товар')
        self.items_tree.heading('quantity', text='Кол-во')
        self.items_tree.heading('unit_price', text='Цена')
        self.items_tree.heading('amount', text='Сумма')
        self.items_tree.pack(fill=tk.BOTH, expand=True)

        # Добавление товара
        add_frame = tk.Frame(self)
        add_frame.grid(row=5, column=0, columnspan=2, sticky='ew', padx=5, pady=5)
        tk.Label(add_frame, text="Товар:").pack(side=tk.LEFT)
        self.product_cb = ttk.Combobox(add_frame, state='readonly')
        self.product_cb.pack(side=tk.LEFT, padx=5)
        tk.Label(add_frame, text="Кол-во:").pack(side=tk.LEFT)
        self.quantity_entry = tk.Entry(add_frame, width=10)
        self.quantity_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(add_frame, text="Цена:").pack(side=tk.LEFT)
        self.price_entry = tk.Entry(add_frame, width=10, state='readonly')
        self.price_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(add_frame, text="Добавить", command=self.add_item).pack(side=tk.LEFT, padx=5)
        tk.Button(add_frame, text="Удалить выбранный", command=self.remove_item).pack(side=tk.LEFT, padx=5)

        tk.Label(self, text="Общая сумма:").grid(row=6, column=0, sticky='e', padx=5, pady=2)
        self.total_label = tk.Label(self, text="0.00")
        self.total_label.grid(row=6, column=1, sticky='w', padx=5, pady=2)

        btn_frame = tk.Frame(self)
        btn_frame.grid(row=7, column=0, columnspan=2, pady=10)
        tk.Button(btn_frame, text="Сохранить", command=self.save).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Отмена", command=self.destroy).pack(side=tk.LEFT, padx=5)

        self.columnconfigure(1, weight=1)
        self.rowconfigure(4, weight=1)

    def load_suppliers_products(self):

        suppliers = fetch_all("SELECT supplier_id, name FROM suppliers ORDER BY name")
        self.supplier_map = {s['name']: s['supplier_id'] for s in suppliers}
        self.supplier_cb['values'] = list(self.supplier_map.keys())

        products = fetch_all("SELECT product_id, name, price FROM products ORDER BY name")
        self.product_map = {p['name']: {'id': p['product_id'], 'price': p['price']} for p in products}
        self.product_cb['values'] = list(self.product_map.keys())
        self.product_cb.bind('<<ComboboxSelected>>', self.on_product_select)

    def on_product_select(self, event):
        name = self.product_cb.get()
        price = self.product_map.get(name, {}).get('price', 0)
        self.price_entry.config(state='normal')
        self.price_entry.delete(0, tk.END)
        self.price_entry.insert(0, str(price))
        self.price_entry.config(state='readonly')

    def add_item(self):
        product_name = self.product_cb.get()
        if not product_name:
            messagebox.showwarning("Ошибка", "Выберите товар")
            return
        try:
            quantity = float(self.quantity_entry.get())
        except ValueError:
            messagebox.showwarning("Ошибка", "Введите корректное количество")
            return
        if quantity <= 0:
            messagebox.showwarning("Ошибка", "Количество должно быть > 0")
            return
        price = float(self.price_entry.get())
        if price <= 0:
            messagebox.showwarning("Ошибка", "Цена должна быть > 0")
            return

        amount = quantity * price
        product_id = self.product_map[product_name]['id']
        self.order_items.append({
            'product_id': product_id,
            'product': product_name,
            'quantity': quantity,
            'unit_price': price,
            'amount': amount
        })
        self.refresh_items_tree()
        self.update_total()

    def remove_item(self):
        selected = self.items_tree.selection()
        if selected:
            idx = int(selected[0])
            del self.order_items[idx]
            self.refresh_items_tree()
            self.update_total()

    def refresh_items_tree(self):
        for row in self.items_tree.get_children():
            self.items_tree.delete(row)
        for i, item in enumerate(self.order_items):
            self.items_tree.insert('', tk.END, iid=str(i), values=(item['product'], item['quantity'], item['unit_price'], item['amount']))

    def update_total(self):
        total = sum(item['amount'] for item in self.order_items)
        self.total_label.config(text=f"{total:.2f}")

    def load_order_data(self):
        # Загружаем данные заказа
        rows = fetch_all("SELECT supplier_id, order_date, delivery_date, status, total_amount FROM orders WHERE order_id=%s", (self.order_id,))
        if rows:
            row = rows[0]
            # Поставщик
            for name, sid in self.supplier_map.items():
                if sid == row['supplier_id']:
                    self.supplier_cb.set(name)
                    break
            self.order_date.insert(0, str(row['order_date']))
            if row['delivery_date']:
                self.delivery_date.insert(0, str(row['delivery_date']))
            self.status_cb.set(row['status'])
            # Товары
            items = fetch_all("""
                SELECT oi.product_id, p.name as product, oi.quantity, oi.unit_price, oi.amount
                FROM order_items oi JOIN products p ON oi.product_id = p.product_id
                WHERE oi.order_id=%s
            """, (self.order_id,))
            for it in items:
                self.order_items.append({
                    'product_id': it['product_id'],
                    'product': it['product'],
                    'quantity': float(it['quantity']),
                    'unit_price': float(it['unit_price']),
                    'amount': float(it['amount'])
                })
            self.refresh_items_tree()
            self.update_total()

    def save(self):
        supplier_name = self.supplier_cb.get()
        if not supplier_name:
            messagebox.showwarning("Ошибка", "Выберите поставщика")
            return
        if not self.order_items:
            messagebox.showwarning("Ошибка", "Добавьте хотя бы один товар")
            return
        supplier_id = self.supplier_map[supplier_name]
        order_date = self.order_date.get()
        delivery_date = self.delivery_date.get() or None
        status = self.status_cb.get()
        total_amount = sum(i['amount'] for i in self.order_items)

        with psycopg2.connect(**DB_PARAMS) as conn:
            with conn.cursor() as cur:
                if self.order_id:
                    cur.execute("""
                        UPDATE orders SET supplier_id=%s, order_date=%s, delivery_date=%s, status=%s, total_amount=%s
                        WHERE order_id=%s
                    """, (supplier_id, order_date, delivery_date, status, total_amount, self.order_id))
                    cur.execute("DELETE FROM order_items WHERE order_id=%s", (self.order_id,))
                else:
                    cur.execute("""
                        INSERT INTO orders (supplier_id, order_date, delivery_date, status, total_amount)
                        VALUES (%s, %s, %s, %s, %s) RETURNING order_id
                    """, (supplier_id, order_date, delivery_date, status, total_amount))
                    self.order_id = cur.fetchone()[0]

                for item in self.order_items:
                    cur.execute("""
                        INSERT INTO order_items (order_id, product_id, quantity, unit_price, amount)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (self.order_id, item['product_id'], item['quantity'], item['unit_price'], item['amount']))

                conn.commit()
        messagebox.showinfo("Успех", "Заказ сохранён")
        self.parent.load_orders()
        self.destroy()