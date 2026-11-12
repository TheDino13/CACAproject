  CREATE TABLE IF NOT EXISTS menu_items (
      id SERIAL PRIMARY KEY,
      name VARCHAR(120) NOT NULL,
      description TEXT NOT NULL DEFAULT '',
      price NUMERIC(10, 2) NOT NULL CHECK (price >= 0)
  );

  INSERT INTO menu_items (name, description, price) VALUES
      ('Margherita', 'Tomato, mozzarella, basil', 8.50),
      ('Pepperoni', 'Tomato, mozzarella, pepperoni', 10.00);
      