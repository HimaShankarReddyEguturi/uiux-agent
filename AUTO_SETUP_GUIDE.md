# 🚀 Auto Unique Figma Files Setup

This creates **unique Figma URLs** for each PDF upload automatically.

## ⚡ Quick Start

### 1. Install Server Dependencies
```bash
cd figma-plugin
npm install express cors uuid
```

### 2. Start Auto Server
```bash
cd figma-plugin
node auto-server.js
```

### 3. Update Your Figma Plugin
- Add content from `auto-plugin.js` to your existing `code.js`
- Or replace your plugin code entirely

### 4. Test Upload
- Upload any PDF (Coding Agent, Healthcare, etc.)
- Get **unique Figma URL** for each upload
- Each PDF creates **new untitled file** in Figma

## 🔄 How It Works

### Before (Current):
```
Upload PDF → Same hardcoded URL → Manual plugin
```

### After (Auto):
```
Upload PDF → Unique URL → Auto-generated design
```

## 📋 What Happens Now

### 1. Upload Coding Agent PDF:
- **URL**: `figma.com/file/abc123def/Coding-Agent?m=auto&t=1234567890`
- **File**: New "Coding Agent" file created
- **Design**: Auto-generated coding interface

### 2. Upload Healthcare PDF:
- **URL**: `figma.com/file/xyz789ghi/Healthcare-App?m=auto&t=1234567891`  
- **File**: New "Healthcare App" file created
- **Design**: Auto-generated medical interface

### 3. Upload Banking PDF:
- **URL**: `figma.com/file/mno456pqr/Banking-System?m=auto&t=1234567892`
- **File**: New "Banking System" file created
- **Design**: Auto-generated financial interface

## ✅ Benefits

- **✅ Unique URLs** - Different for each PDF
- **✅ Auto Creation** - No manual plugin steps
- **✅ Custom Names** - Based on PDF content
- **✅ Fresh Files** - New untitled file each time
- **✅ Fallback Safe** - Uses existing system if fails

## 🛡️ Safety Features

- **Automatic Fallback** - If auto creation fails, uses your existing system
- **No Breaking Changes** - Your current code still works
- **Error Handling** - Graceful degradation
- **Timeout Protection** - Won't hang indefinitely

## 🔧 Files Modified

- **✅ `app/main.py`** - Enhanced with auto creation (fallback preserved)
- **➕ `figma_auto.py`** - New auto client
- **➕ `auto-server.js`** - New server for file creation
- **➕ `auto-plugin.js`** - New plugin code

## 🎯 Result

**Every PDF upload now creates a unique Figma file with custom design!**

No more hardcoded URLs - each upload gets its own fresh file.