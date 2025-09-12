const express = require('express');
const app = express();
const port = 8000;

// Middleware
app.use(express.json());

// In-memory storage (equivalent to Python list)
let items = [];
let nextId = 1;

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ status: 'healthy', message: 'Service is running' });
});

// Root endpoint
app.get('/', (req, res) => {
    res.json({ message: 'CRUD API Service', version: '1.0.0' });
});

// Get all items
app.get('/items', (req, res) => {
    const { category } = req.query;
    let filteredItems = items;
    
    if (category) {
        filteredItems = items.filter(item => 
            item.category.toLowerCase() === category.toLowerCase()
        );
    }
    
    res.json(filteredItems);
});

// Get item by ID
app.get('/items/:id', (req, res) => {
    const id = parseInt(req.params.id);
    const item = items.find(item => item.id === id);
    
    if (!item) {
        return res.status(404).json({ error: 'Item not found' });
    }
    
    res.json(item);
});

// Create new item
app.post('/items', (req, res) => {
    const { name, price, category } = req.body;
    
    if (!name || price === undefined || !category) {
        return res.status(422).json({ 
            error: 'Missing required fields: name, price, category' 
        });
    }
    
    const newItem = {
        id: nextId++,
        name,
        price: parseFloat(price),
        category
    };
    
    items.push(newItem);
    res.status(201).json(newItem);
});

// Update item
app.put('/items/:id', (req, res) => {
    const id = parseInt(req.params.id);
    const itemIndex = items.findIndex(item => item.id === id);
    
    if (itemIndex === -1) {
        return res.status(404).json({ error: 'Item not found' });
    }
    
    const { name, price, category } = req.body;
    const item = items[itemIndex];
    
    if (name !== undefined) item.name = name;
    if (price !== undefined) item.price = parseFloat(price);
    if (category !== undefined) item.category = category;
    
    res.json(item);
});

// Delete item
app.delete('/items/:id', (req, res) => {
    const id = parseInt(req.params.id);
    const itemIndex = items.findIndex(item => item.id === id);
    
    if (itemIndex === -1) {
        return res.status(404).json({ error: 'Item not found' });
    }
    
    items.splice(itemIndex, 1);
    res.status(204).send();
});

// Start server
app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
});
