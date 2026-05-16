import express from 'express';
import cors from 'cors';
import { fileURLToPath } from 'url';
import { dirname } from 'path';
import fs from 'fs';
import path from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const app = express();
const PORT = 3001;

// Middleware
app.use(cors());
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ limit: '50mb', extended: true }));

// Create temp directory if it doesn't exist
const tempDir = path.join(__dirname, 'temp');
if (!fs.existsSync(tempDir)) {
  fs.mkdirSync(tempDir, { recursive: true });
}

// Endpoint to save photos
app.post('/api/save-photo', (req, res) => {
  try {
    const { photo } = req.body;
    
    if (!photo) {
      return res.status(400).json({ error: 'No photo provided' });
    }

    // Extract base64 data from data URL
    const base64Data = photo.replace(/^data:image\/\w+;base64,/, '');
    
    // Create filename with timestamp
    const timestamp = Date.now();
    const filename = `photo-${timestamp}.png`;
    const filepath = path.join(tempDir, filename);

    // Save file
    fs.writeFileSync(filepath, base64Data, 'base64');
    
    res.json({
      success: true,
      filename,
      path: filepath
    });
  } catch (error) {
    console.error('Error saving photo:', error);
    res.status(500).json({ error: 'Failed to save photo' });
  }
});

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

app.listen(PORT, () => {
  console.log(`Photo booth backend running on http://localhost:${PORT}`);
});
