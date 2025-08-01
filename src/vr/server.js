const express = require('express');
const path = require('path');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const multer = require('multer');
require('dotenv').config();

const app = express();
const PORT = process.env.WEB_PORT || 3000;

// Security and performance middleware
app.use(helmet({
    contentSecurityPolicy: {
        directives: {
            defaultSrc: ["'self'"],
            scriptSrc: ["'self'", "'unsafe-inline'", "'unsafe-eval'", "https://aframe.io", "https://cdn.aframe.io"],
            styleSrc: ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
            fontSrc: ["'self'", "https://fonts.gstatic.com"],
            imgSrc: ["'self'", "data:", "blob:", "https:"],
            connectSrc: ["'self'", "ws:", "wss:"],
            objectSrc: ["'none'"],
            mediaSrc: ["'self'", "blob:", "data:"],
            frameSrc: ["'self'"]
        }
    }
}));

app.use(compression());
app.use(cors());
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// Serve static files
app.use('/static', express.static(path.join(__dirname, 'public')));
app.use('/assets', express.static(path.join(__dirname, 'vr-content/assets')));
app.use('/models', express.static(path.join(__dirname, 'vr-content/models')));
app.use('/textures', express.static(path.join(__dirname, 'vr-content/textures')));

// Configure multer for file uploads
const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        cb(null, path.join(__dirname, 'vr-content/assets'));
    },
    filename: (req, file, cb) => {
        const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
        cb(null, file.fieldname + '-' + uniqueSuffix + path.extname(file.originalname));
    }
});

const upload = multer({ 
    storage,
    limits: { fileSize: 100 * 1024 * 1024 }, // 100MB limit
    fileFilter: (req, file, cb) => {
        const allowedTypes = [
            'model/gltf+json', 'model/gltf-binary',
            'image/jpeg', 'image/png', 'image/webp',
            'audio/mpeg', 'audio/wav', 'audio/ogg',
            'video/mp4', 'video/webm'
        ];
        
        if (allowedTypes.includes(file.mimetype)) {
            cb(null, true);
        } else {
            cb(new Error('Invalid file type'), false);
        }
    }
});

// VR Learning Environments
const vrEnvironments = {
    'networking-lab': {
        title: 'Virtual Networking Lab',
        description: 'Hands-on networking configuration in VR',
        scene: 'networking-lab.html',
        category: 'technical',
        skills: ['networking', 'cisco', 'routing', 'switching'],
        difficulty: 'intermediate',
        duration: '45 minutes'
    },
    'programming-space': {
        title: 'Immersive Coding Environment',
        description: '3D programming workspace with virtual IDE',
        scene: 'programming-space.html',
        category: 'programming',
        skills: ['python', 'javascript', 'coding'],
        difficulty: 'beginner',
        duration: '30 minutes'
    },
    'data-center': {
        title: 'Virtual Data Center Tour',
        description: 'Explore cloud infrastructure and server management',
        scene: 'data-center.html',
        category: 'cloud',
        skills: ['cloud computing', 'infrastructure', 'devops'],
        difficulty: 'intermediate',
        duration: '60 minutes'
    },
    'security-lab': {
        title: 'Cybersecurity Command Center',
        description: 'Interactive security monitoring and incident response',
        scene: 'security-lab.html',
        category: 'security',
        skills: ['cybersecurity', 'incident response', 'monitoring'],
        difficulty: 'advanced',
        duration: '90 minutes'
    },
    'ai-workshop': {
        title: 'AI/ML Visualization Studio',
        description: 'Visualize and interact with machine learning models',
        scene: 'ai-workshop.html',
        category: 'artificial-intelligence',
        skills: ['machine learning', 'data science', 'ai'],
        difficulty: 'advanced',
        duration: '75 minutes'
    }
};

// Routes

// Health check
app.get('/health', (req, res) => {
    res.json({ 
        status: 'healthy', 
        timestamp: new Date().toISOString(),
        service: 'VR Learning Environments'
    });
});

// Main VR portal page
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Get all VR environments
app.get('/api/environments', (req, res) => {
    res.json({
        environments: Object.entries(vrEnvironments).map(([id, env]) => ({
            id,
            ...env
        }))
    });
});

// Get specific VR environment
app.get('/api/environments/:id', (req, res) => {
    const { id } = req.params;
    const environment = vrEnvironments[id];
    
    if (!environment) {
        return res.status(404).json({ error: 'Environment not found' });
    }
    
    res.json({ id, ...environment });
});

// Serve VR scenes
app.get('/vr/:scene', (req, res) => {
    const { scene } = req.params;
    const scenePath = path.join(__dirname, 'scenes', scene);
    
    // Check if scene exists
    if (!require('fs').existsSync(scenePath)) {
        return res.status(404).json({ error: 'VR scene not found' });
    }
    
    res.sendFile(scenePath);
});

// Upload VR content
app.post('/api/upload', upload.single('file'), (req, res) => {
    if (!req.file) {
        return res.status(400).json({ error: 'No file uploaded' });
    }
    
    res.json({
        success: true,
        filename: req.file.filename,
        originalName: req.file.originalname,
        size: req.file.size,
        url: `/assets/${req.file.filename}`
    });
});

// Create new VR learning session
app.post('/api/sessions', (req, res) => {
    const { environmentId, userId, settings } = req.body;
    
    if (!vrEnvironments[environmentId]) {
        return res.status(400).json({ error: 'Invalid environment ID' });
    }
    
    const sessionId = require('crypto').randomUUID();
    
    // Store session data (in production, use a database)
    const session = {
        id: sessionId,
        environmentId,
        userId,
        settings: settings || {},
        createdAt: new Date().toISOString(),
        status: 'active'
    };
    
    res.json({ session });
});

// Get VR session data
app.get('/api/sessions/:sessionId', (req, res) => {
    const { sessionId } = req.params;
    
    // In production, fetch from database
    res.json({
        session: {
            id: sessionId,
            status: 'active',
            progress: 45,
            timeSpent: 1200, // seconds
            completedTasks: 3,
            totalTasks: 7
        }
    });
});

// Update session progress
app.put('/api/sessions/:sessionId/progress', (req, res) => {
    const { sessionId } = req.params;
    const { progress, completedTasks, timeSpent } = req.body;
    
    // Update session in database
    res.json({
        success: true,
        sessionId,
        progress,
        completedTasks,
        timeSpent
    });
});

// Complete VR session
app.post('/api/sessions/:sessionId/complete', (req, res) => {
    const { sessionId } = req.params;
    const { score, achievements, feedback } = req.body;
    
    res.json({
        success: true,
        sessionId,
        completionData: {
            score,
            achievements: achievements || [],
            feedback,
            completedAt: new Date().toISOString(),
            certificateEarned: score >= 80
        }
    });
});

// Get VR analytics
app.get('/api/analytics', (req, res) => {
    res.json({
        analytics: {
            totalSessions: 1250,
            averageSessionTime: 35.5, // minutes
            completionRate: 78.3,
            popularEnvironments: [
                { id: 'programming-space', sessions: 450 },
                { id: 'networking-lab', sessions: 380 },
                { id: 'data-center', sessions: 220 }
            ],
            userFeedback: {
                averageRating: 4.6,
                totalReviews: 892
            }
        }
    });
});

// Error handling middleware
app.use((error, req, res, next) => {
    console.error('Error:', error);
    
    if (error instanceof multer.MulterError) {
        if (error.code === 'LIMIT_FILE_SIZE') {
            return res.status(400).json({ error: 'File too large' });
        }
    }
    
    res.status(500).json({ error: 'Internal server error' });
});

// 404 handler
app.use((req, res) => {
    res.status(404).json({ error: 'Route not found' });
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
    console.log(`🥽 VR Learning Server running on port ${PORT}`);
    console.log(`🌐 Access VR environments at http://localhost:${PORT}`);
    console.log(`📊 Available environments: ${Object.keys(vrEnvironments).length}`);
});

module.exports = app; 