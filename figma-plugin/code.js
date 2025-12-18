figma.showUI(__html__, { width: 420, height: 580 })

const FRAME_WIDTH = 1440
const FRAME_HEIGHT = 1024
const FRAME_GAP = 120
const FRAMES_PER_ROW = 2

// ---------- AUTO RUN / FETCH ----------

figma.on('run', async () => {
  try {
    await autoFetchAndRender()
  } catch (error) {
    console.log('Auto-render failed, showing UI:', error)
  }
})

async function autoFetchAndRender() {
  try {
    const response = await fetch('http://localhost:8000/latest-report')
    if (response.ok) {
      const data = await response.json()
      if (data.status === 'success' && data.report) {
        await renderUIPayload(data.report)
        figma.notify('Design auto-generated from latest upload!')
        figma.closePlugin()
        return true
      }
    }
  } catch (error) {
    console.log('Auto-fetch failed:', error)
  }
  return false
}

// ---------- UI MESSAGE HANDLERS ----------

figma.ui.onmessage = async (message) => {
  if (message.type === 'AUTO_FETCH') {
    const ok = await autoFetchAndRender()
    if (!ok) {
      figma.ui.postMessage({
        type: 'STATUS',
        payload: { ok: false, message: 'No recent reports found' },
      })
    }
    return
  }

  if (message.type === 'GENERATE_UI') {
    try {
      figma.currentPage.name
      figma.root.children

      if (!message.payload) throw new Error('No payload received')

      let screens = []
      if (Array.isArray(message.payload.screens)) {
        screens = message.payload.screens
      } else if (message.payload.report && Array.isArray(message.payload.report.screens)) {
        screens = message.payload.report.screens
      }
      if (screens.length === 0) throw new Error('No screens to render')

      const renderPayload = {
        project_name:
          message.payload.project_name ||
          (message.payload.report && message.payload.report.project_name) ||
          'Generated UI',
        screens: screens,
        styles:
          message.payload.styles ||
          (message.payload.report && message.payload.report.styles) ||
          {},
        navigation_flow: message.payload.navigation_flow || [],
      }

      await renderUIPayload(renderPayload)
      figma.ui.postMessage({ type: 'STATUS', payload: { ok: true } })
      figma.notify('Screens generated successfully.')
    } catch (error) {
      const msg = error && error.message ? error.message : String(error)
      figma.ui.postMessage({
        type: 'STATUS',
        payload: { ok: false, message: 'Render failed: ' + msg },
      })
      figma.notify('Failed to render UI: ' + msg, { error: true })
    }
  }
}

// ---------- RENDER MAIN ----------

async function renderUIPayload(report) {
  await ensureFonts()

  const page = figma.currentPage
  page.name = report.project_name || 'Auto Generated UI'

  const screens = Array.isArray(report.screens) ? report.screens : []
  const styles = report.styles || {}
  const colors = styles.colors || {}
  const navigationFlow = report.navigation_flow || []

  const theme = styles.theme || 'default'
  const themeDefaults = getThemeDefaults(theme)

  page.children.forEach((n) => n.remove())

  const frameMap = new Map()

  screens.forEach((screen, index) => {
    const frame = createScreenFrame(screen, index, colors, themeDefaults)
    page.appendChild(frame)
    buildLayoutSections(frame, screen.layout || {}, colors, themeDefaults, screen.interactions || [])
    frameMap.set(screen.name, frame)
  })

  createPrototypeConnections(frameMap, navigationFlow)

  figma.viewport.center = { x: 0, y: 0 }
  figma.currentPage.selection = []
}

// ---------- THEMES ----------

function getThemeDefaults(theme) {
  switch (theme) {
    case 'security':
      return {
        surface: '#FFFFFF',
        accent: '#DC2626',
        gradient: 'linear #FF6B6B → #4ECDC4',
      }
    case 'analytics':
      return {
        surface: '#0B1120',
        accent: '#38BDF8',
        gradient: 'linear #0EA5E9 → #22C55E',
      }
    case 'testing':
      return {
        surface: '#FFFFFF',
        accent: '#7C3AED',
        gradient: 'linear #6366F1 → #EC4899',
      }
    default:
      return {
        surface: '#FFFFFF',
        accent: '#0F172A',
        gradient: 'linear #FF6B6B → #4ECDC4',
      }
  }
}

// ---------- SCREEN FRAME ----------

function createScreenFrame(screen, index, colors, themeDefaults) {
  const frame = figma.createFrame()
  frame.name = screen.name || 'Screen ' + (index + 1)
  frame.resize(FRAME_WIDTH, FRAME_HEIGHT)

  frame.cornerRadius = screen.cornerRadius || 32
  frame.strokeWeight = 2
  frame.strokes = [
    {
      type: 'SOLID',
      color: hexToRgb(colors.accent || themeDefaults.accent),
      opacity: 0.1,
    },
  ]
  frame.fills = [
    {
      type: 'SOLID',
      color: hexToRgb(screen.background || colors.surface || themeDefaults.surface),
    },
  ]

  const column = index % FRAMES_PER_ROW
  const row = Math.floor(index / FRAMES_PER_ROW)
  frame.x = column * (FRAME_WIDTH + FRAME_GAP)
  frame.y = row * (FRAME_HEIGHT + FRAME_GAP)

  const heading = figma.createText()
  heading.characters = screen.title || screen.name || 'Untitled Screen'
  heading.fontSize = screen.titleSize || 48
  heading.fontName = { family: 'Inter', style: 'Bold' }
  heading.x = 64
  heading.y = 48

  const description = figma.createText()
  description.characters =
    screen.description || 'Auto generated based on your PDF/project spec.'
  description.fontSize = 18
  description.lineHeight = { unit: 'PIXELS', value: 26 }
  description.opacity = 0.72
  description.fontName = { family: 'Inter', style: 'Regular' }
  description.x = 64
  description.y = 120

  frame.appendChild(heading)
  frame.appendChild(description)

  return frame
}

// ---------- LAYOUT / SECTIONS ----------

function buildLayoutSections(frame, layout, colors, themeDefaults, interactions) {
  interactions = interactions || []
  const sections = layout.sections || (Array.isArray(layout) ? layout : [])
  if (!sections.length) return

  let currentY = 200

  sections.forEach((section) => {
    const component = createModernComponent(section, colors, themeDefaults, interactions)
    if (component) {
      component.x = section.x != null ? section.x : 64
      component.y = section.y != null ? section.y : currentY
      frame.appendChild(component)
      addComponentInteractions(component, interactions)
      currentY += (component.height || 180) + (section.spacing || 32)
    }
  })
}

// ---------- FONTS ----------

async function ensureFonts() {
  try {
    await figma.loadFontAsync({ family: 'Inter', style: 'Regular' })
    await figma.loadFontAsync({ family: 'Inter', style: 'Bold' })
  } catch (err) {
    try {
      await figma.loadFontAsync({ family: 'Roboto', style: 'Regular' })
      await figma.loadFontAsync({ family: 'Roboto', style: 'Bold' })
    } catch (err2) {
      throw new Error('Could not load any fonts')
    }
  }
}

// ---------- COMPONENT FACTORY ----------

function createModernComponent(section, colors, themeDefaults, interactions) {
  interactions = interactions || []
  const type = section.component

  switch (type) {
    case 'gradient_banner':
      return createGradientBanner(section, themeDefaults)
    case 'filter_chips':
      return createFilterChips(section)
    case 'event_cards':
      return createEventCards(section)
    case 'elevated_container':
      return createElevatedContainer(section)
    case 'section_heading':
      return createSectionHeading(section)
    case 'rounded_card':
      return createRoundedCard(section)
    case 'bottom_sheet':
      return createBottomSheet(section)
    case 'floating_action_button':
      return createFloatingActionButton(section)
    default:
      return createBasicComponent(section, colors, themeDefaults)
  }
}

function createGradientBanner(section, themeDefaults) {
  const banner = figma.createFrame()
  banner.name = 'Gradient Banner'
  banner.resize(1312, section.height || 260)
  banner.cornerRadius = section.cornerRadius || 24

  const gradStr = section.gradient || themeDefaults.gradient
  const colors = parseGradient(gradStr)
  banner.fills = [
    {
      type: 'GRADIENT_LINEAR',
      gradientTransform: [
        [1, 0, 0],
        [0, 1, 0],
      ],
      gradientStops: [
        { position: 0, color: colors[0] },
        { position: 1, color: colors[1] },
      ],
    },
  ]

  banner.effects = [
    {
      type: 'DROP_SHADOW',
      color: hexToRgba('#000000', 0.22),
      offset: { x: 0, y: 10 },
      radius: 32,
      blendMode: 'NORMAL',
      visible: true,
    },
  ]

  const title = figma.createText()
  title.characters = section.title || 'Featured Content'
  title.fontSize = section.titleSize || 40
  title.fontName = { family: 'Inter', style: 'Bold' }
  title.fills = [{ type: 'SOLID', color: hexToRgb(section.text_color || '#FFFFFF') }]
  title.x = 40
  title.y = 40
  banner.appendChild(title)

  return banner
}

function createFilterChips(section) {
  const container = figma.createFrame()
  container.name = 'Filter Chips'
  container.resize(1312, 80)
  container.fills = []

  const items = section.items || ['Primary', 'Secondary', 'Tertiary']
  let currentX = 0

  items.forEach((item, index) => {
    const chip = figma.createFrame()
    chip.name = 'Chip ' + (index + 1)
    const w = section.chipWidth || 120
    const h = section.chipHeight || 44
    chip.resize(w, h)
    chip.cornerRadius = 999

    const active =
      section.activeIndex != null ? index === section.activeIndex : index === 0
    chip.fills = [
      {
        type: 'SOLID',
        color: hexToRgb(
          active ? section.activeColor || '#FF6B6B' : section.inactiveColor || '#F8F9FA'
        ),
      },
    ]
    chip.effects = [
      {
        type: 'DROP_SHADOW',
        color: hexToRgba('#000000', 0.1),
        offset: { x: 0, y: 4 },
        radius: 15,
        blendMode: 'NORMAL',
        visible: true,
      },
    ]

    const text = figma.createText()
    text.characters = item
    text.fontSize = 15
    text.fontName = { family: 'Inter', style: 'Regular' }
    text.fills = [
      {
        type: 'SOLID',
        color: hexToRgb(active ? '#FFFFFF' : '#111827'),
      },
    ]
    text.textAlignHorizontal = 'CENTER'
    text.textAlignVertical = 'CENTER'
    text.resize(w, h)
    chip.appendChild(text)

    chip.x = currentX
    currentX += w + (section.chipGap || 16)
    container.appendChild(chip)
  })

  return container
}

function createEventCards(section) {
  const container = figma.createFrame()
  container.name = 'Event Cards'
  const columns = section.grid_columns || 2
  const cardWidth = (1312 - (columns - 1) * 16) / columns
  container.resize(1312, section.height || 320)
  container.fills = []

  for (let i = 0; i < columns; i++) {
    const card = figma.createFrame()
    card.name = section.title || 'Event Card ' + (i + 1)
    card.resize(cardWidth, section.cardHeight || 260)
    card.cornerRadius = section.cornerRadius || 24

    const gradStr = section.gradient || 'linear #6366F1 → #EC4899'
    const colors = parseGradient(gradStr)
    card.fills = [
      {
        type: 'GRADIENT_LINEAR',
        gradientTransform: [
          [1, 0, 0],
          [0, 1, 0],
        ],
        gradientStops: [
          { position: 0, color: colors[0] },
          { position: 1, color: colors[1] },
        ],
      },
    ]

    card.effects = [
      {
        type: 'DROP_SHADOW',
        color: hexToRgba('#000000', 0.14),
        offset: { x: 0, y: 10 },
        radius: 32,
        blendMode: 'NORMAL',
        visible: true,
      },
    ]

    const cardText = figma.createText()
    cardText.characters = section.cardTitle || 'Event ' + (i + 1)
    cardText.fontSize = 20
    cardText.fontName = { family: 'Inter', style: 'Bold' }
    cardText.fills = [{ type: 'SOLID', color: hexToRgb('#FFFFFF') }]
    cardText.x = 24
    cardText.y = 24
    card.appendChild(cardText)

    card.x = i * (cardWidth + 16)
    container.appendChild(card)
  }

  return container
}

function createElevatedContainer(section) {
  const container = figma.createFrame()
  container.name = 'Elevated Container'
  container.resize(1312, section.height || 160)
  container.cornerRadius = section.cornerRadius || 22

  const gradStr = section.gradient || 'linear #F97316 → #EC4899'
  const colors = parseGradient(gradStr)
  container.fills = [
    {
      type: 'GRADIENT_LINEAR',
      gradientTransform: [
        [1, 0, 0],
        [0, 1, 0],
      ],
      gradientStops: [
        { position: 0, color: colors[0] },
        { position: 1, color: colors[1] },
      ],
    },
  ]

  container.effects = [
    {
      type: 'DROP_SHADOW',
      color: hexToRgba('#F97316', 0.35),
      offset: { x: 0, y: 12 },
      radius: 40,
      blendMode: 'NORMAL',
      visible: true,
    },
  ]

  const text = figma.createText()
  text.characters = section.title || 'Elevated Content'
  text.fontSize = 22
  text.fontName = { family: 'Inter', style: 'Bold' }
  text.fills = [{ type: 'SOLID', color: hexToRgb('#FFFFFF') }]
  text.x = 28
  text.y = 64
  container.appendChild(text)

  return container
}

function createSectionHeading(section) {
  const container = figma.createFrame()
  container.name = 'Section Heading'
  container.resize(1312, 80)

  if (section.background) {
    container.fills = [{ type: 'SOLID', color: hexToRgb(section.background) }]
    container.cornerRadius = 16
  } else {
    container.fills = []
  }

  const heading = figma.createText()
  heading.characters = section.title || 'Section Title'
  heading.fontSize = section.titleSize || 26
  heading.fontName = { family: 'Inter', style: 'Bold' }
  const textColor = section.text_color || (section.background ? '#FFFFFF' : '#111827')
  heading.fills = [{ type: 'SOLID', color: hexToRgb(textColor) }]
  heading.x = 24
  heading.y = 26
  container.appendChild(heading)

  return container
}

function createRoundedCard(section) {
  const card = figma.createFrame()
  card.name = 'Rounded Card'
  card.resize(1312, section.height || 200)
  card.cornerRadius = section.cornerRadius || 24

  if (section.background && section.background.indexOf('linear') !== -1) {
    const colors = parseGradient(section.background)
    card.fills = [
      {
        type: 'GRADIENT_LINEAR',
        gradientTransform: [
          [1, 0, 0],
          [0, 1, 0],
        ],
        gradientStops: [
          { position: 0, color: colors[0] },
          { position: 1, color: colors[1] },
        ],
      },
    ]
  } else {
    const bg = section.background || '#FFFFFF'
    card.fills = [{ type: 'SOLID', color: hexToRgb(bg) }]
  }

  card.effects = [
    {
      type: 'DROP_SHADOW',
      color: hexToRgba('#000000', 0.12),
      offset: { x: 0, y: 8 },
      radius: 30,
      blendMode: 'NORMAL',
      visible: true,
    },
  ]

  const text = figma.createText()
  text.characters = section.title || 'Rounded Card Content'
  text.fontSize = 18
  text.fontName = { family: 'Inter', style: 'Regular' }
  const textColor =
    section.text_color || (section.background && section.background !== '#FFFFFF' ? '#FFFFFF' : '#111827')
  text.fills = [{ type: 'SOLID', color: hexToRgb(textColor) }]
  text.x = 24
  text.y = 24
  card.appendChild(text)

  return card
}

function createBottomSheet(section) {
  const sheet = figma.createFrame()
  sheet.name = 'Bottom Sheet'
  sheet.resize(1312, section.height || 380)
  sheet.cornerRadius = section.cornerRadius || 32

  if (section.background && section.background.indexOf('linear') !== -1) {
    const colors = parseGradient(section.background)
    sheet.fills = [
      {
        type: 'GRADIENT_LINEAR',
        gradientTransform: [
          [1, 0, 0],
          [0, 1, 0],
        ],
        gradientStops: [
          { position: 0, color: colors[0] },
          { position: 1, color: colors[1] },
        ],
      },
    ]
  } else {
    const bg = section.background || '#FFFFFF'
    sheet.fills = [{ type: 'SOLID', color: hexToRgb(bg) }]
  }

  sheet.effects = [
    {
      type: 'DROP_SHADOW',
      color: hexToRgba('#000000', 0.2),
      offset: { x: 0, y: -8 },
      radius: 24,
      blendMode: 'NORMAL',
      visible: true,
    },
    {
      type: 'DROP_SHADOW',
      color: hexToRgba('#000000', 0.1),
      offset: { x: 0, y: -2 },
      radius: 8,
      blendMode: 'NORMAL',
      visible: true,
    },
  ]

  const handle = figma.createFrame()
  handle.name = 'Handle'
  handle.resize(48, 4)
  handle.cornerRadius = 2
  const handleColor =
    section.handleColor || (section.background && section.background !== '#FFFFFF' ? '#FFFFFF' : '#D1D5DB')
  handle.fills = [{ type: 'SOLID', color: hexToRgb(handleColor) }]
  handle.x = (sheet.width - handle.width) / 2
  handle.y = 12
  sheet.appendChild(handle)

  const content = figma.createText()
  content.characters =
    section.title || section.total || 'Bottom Sheet Content – swipe up for more details'
  content.fontSize = 18
  content.fontName = { family: 'Inter', style: 'Regular' }
  const textColor =
    section.text_color || (section.background && section.background !== '#FFFFFF' ? '#FFFFFF' : '#111827')
  content.fills = [{ type: 'SOLID', color: hexToRgb(textColor) }]
  content.textAlignHorizontal = 'CENTER'
  content.x = 32
  content.y = 52
  content.resize(sheet.width - 64, 100)
  sheet.appendChild(content)

  return sheet
}

function createFloatingActionButton(section) {
  const fab = figma.createFrame()
  fab.name = 'Floating Action Button'
  const size = section.size || 64
  fab.resize(size, size)
  fab.cornerRadius = size / 2

  const gradStr = section.gradient || 'linear #22C55E → #16A34A'
  const colors = parseGradient(gradStr)
  fab.fills = [
    {
      type: 'GRADIENT_LINEAR',
      gradientTransform: [
        [1, 0, 0],
        [0, 1, 0],
      ],
      gradientStops: [
        { position: 0, color: colors[0] },
        { position: 1, color: colors[1] },
      ],
    },
  ]

  fab.effects = [
    {
      type: 'DROP_SHADOW',
      color: hexToRgba('#22C55E', 0.4),
      offset: { x: 0, y: 8 },
      radius: 16,
      blendMode: 'NORMAL',
      visible: true,
    },
  ]

  const icon = figma.createText()
  icon.characters = section.icon || '+'
  icon.fontSize = section.iconSize || 30
  icon.fontName = { family: 'Inter', style: 'Bold' }
  icon.fills = [{ type: 'SOLID', color: hexToRgb('#FFFFFF') }]
  icon.textAlignHorizontal = 'CENTER'
  icon.textAlignVertical = 'CENTER'
  icon.resize(fab.width, fab.height)
  fab.appendChild(icon)

  return fab
}

function createBasicComponent(section, colors, themeDefaults) {
  const container = figma.createFrame()
  container.name = section.component || 'Component'
  container.resize(1312, section.height || 120)
  container.cornerRadius = section.cornerRadius || 16
  container.fills = [
    {
      type: 'SOLID',
      color: hexToRgb(
        section.background || colors.surface || themeDefaults.surface || '#F8F9FA'
      ),
    },
  ]

  const text = figma.createText()
  text.characters =
    section.title || (section.component || 'Component') + ' – auto generated content'
  text.fontSize = 14
  text.fontName = { family: 'Inter', style: 'Regular' }
  text.x = 16
  text.y = 16
  container.appendChild(text)

  return container
}

// ---------- PROTOTYPE / INTERACTIONS ----------

function createPrototypeConnections(frameMap, navigationFlow) {
  navigationFlow = navigationFlow || []
  navigationFlow.forEach((nav) => {
    const fromFrame = frameMap.get(nav.from_screen)
    const toFrame = frameMap.get(nav.to_screen)

    if (fromFrame && toFrame) {
      const triggerNode = findComponentByType(fromFrame, nav.trigger_component || '')
      if (triggerNode) {
        const interaction = nav.interaction || {}
        const reaction = {
          action: {
            type: 'NODE',
            destinationId: toFrame.id,
            navigation: 'NAVIGATE',
            transition: getTransitionType(interaction.transition),
            preserveScrollPosition: false,
          },
          trigger: {
            type: interaction.trigger === 'onHover' ? 'ON_HOVER' : 'ON_CLICK',
          },
        }
        triggerNode.reactions = [reaction]
      }
    }
  })
}

function addComponentInteractions(component, interactions) {
  interactions = interactions || []
  interactions.forEach((interaction) => {
    if (interaction.action === 'toggle' || interaction.action === 'overlay') {
      component.effects = component.effects || []
      component.effects.push({
        type: 'DROP_SHADOW',
        color: { r: 0, g: 0, b: 0, a: 0.1 },
        offset: { x: 0, y: 2 },
        radius: 8,
        blendMode: 'NORMAL',
        visible: true,
      })
    }
  })
}

function findComponentByType(frame, componentType) {
  const lowered = (componentType || '').toLowerCase()
  for (const child of frame.children) {
    if (lowered && child.name.toLowerCase().indexOf(lowered) !== -1) return child
    if ('children' in child && child.children.length > 0) {
      const found = findComponentByType(child, componentType)
      if (found) return found
    }
  }
  return frame
}

function getTransitionType(transition) {
  switch (transition) {
    case 'slide_left':
      return { type: 'SLIDE_IN', direction: 'LEFT' }
    case 'slide_right':
      return { type: 'SLIDE_IN', direction: 'RIGHT' }
    case 'fade':
      return { type: 'DISSOLVE' }
    case 'push':
      return { type: 'PUSH' }
    default:
      return { type: 'SLIDE_IN', direction: 'LEFT' }
  }
}

// ---------- HELPERS ----------

function parseGradient(gradientStr) {
  const colors = gradientStr.match(/#[A-Fa-f0-9]{6}/g) || ['#FF6B6B', '#4ECDC4']
  return colors.map(function (hex) {
    return hexToRgba(hex, 1)
  })
}

function hexToRgb(hex) {
  const sanitized = hex.replace('#', '')
  const bigint = parseInt(sanitized, 16)
  const r = (bigint >> 16) & 255
  const g = (bigint >> 8) & 255
  const b = bigint & 255
  return { r: r / 255, g: g / 255, b: b / 255 }
}

function hexToRgba(hex, alpha) {
  if (alpha === void 0) alpha = 1
  const sanitized = hex.replace('#', '')
  const bigint = parseInt(sanitized, 16)
  const r = (bigint >> 16) & 255
  const g = (bigint >> 8) & 255
  const b = bigint & 255
  return { r: r / 255, g: g / 255, b: b / 255, a: alpha }
}

