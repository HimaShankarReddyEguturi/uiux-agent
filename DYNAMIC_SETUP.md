# Dynamic File Creation Setup (Optional Enhancement)

This adds dynamic Figma file creation without modifying your existing code.

## 🚀 Quick Setup

### 1. Install Plugin Server Dependencies
```bash
cd figma-plugin
npm install
```

### 2. Add Environment Variables (Optional)
Add to your `.env` file:
```env
# Enable dynamic file creation (optional)
ENABLE_DYNAMIC_FILES=true
FIGMA_PLUGIN_API_URL=http://localhost:3001
FIGMA_PLUGIN_PORT=3001
```

### 3. Start Plugin Server (Optional)
```bash
cd figma-plugin
npm start
```

### 4. Update Figma Plugin
Add the content from `dynamic-code.js` to your existing `code.js` file.

## 🔄 How It Works

### Current System (Unchanged)
- Upload PDF → Generate JSON → Return hardcoded Figma URL
- All existing functionality works exactly the same

### Enhanced System (Optional)
- Upload PDF → Generate JSON → Try dynamic creation → Fallback to existing system
- If dynamic creation fails, uses your current hardcoded URLs

## 📁 New Files Created

- `app/services/figma_dynamic.py` - Dynamic file creation client
- `figma-plugin/plugin-server.js` - Plugin communication server  
- `figma-plugin/dynamic-code.js` - Enhanced plugin code
- `app/main_enhanced.py` - Enhanced main with fallback logic

## ✅ Benefits

- **Zero Breaking Changes** - Existing system unchanged
- **Optional Feature** - Enable/disable with environment variable
- **Automatic Fallback** - Uses existing system if dynamic fails
- **Gradual Rollout** - Test without affecting current users

## 🔧 Usage

### Option 1: Keep Current System
- Don't set `ENABLE_DYNAMIC_FILES=true`
- Everything works exactly as before

### Option 2: Enable Dynamic Creation
- Set `ENABLE_DYNAMIC_FILES=true`
- Start plugin server
- Get dynamic file creation with fallback

## 🛡️ Safety

- Your existing code is **completely untouched**
- All current endpoints work exactly the same
- Dynamic creation is **purely additive**
- Automatic fallback ensures **zero downtime**