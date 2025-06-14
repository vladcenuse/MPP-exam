<script setup lang="ts">
import { ref, computed, onUnmounted, onMounted } from 'vue'
import { Pie } from 'vue-chartjs'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'
import characterImage from './assets/chisu.png'
import { CharacterService, type Character } from './services/CharacterService'

ChartJS.register(ArcElement, Tooltip, Legend)

const characters = ref<Character[]>([])
const selectedCharacter = ref<Character | null>(null)
const showAddForm = ref(false)
const isAutoGenerating = ref(false)
const isEditing = ref(false)
const isLoading = ref(true)
const error = ref<string | null>(null)
let ws: WebSocket | null = null

// WebSocket setup
const setupWebSocket = () => {
  if (ws) {
    console.log('Closing existing WebSocket connection')
    ws.close()
  }

  try {
    console.log('Attempting to connect to WebSocket...')
    ws = new WebSocket('ws://localhost:8000/ws')
    
    ws.onopen = () => {
      console.log('%cWebSocket Connected ✅', 'color: #00ff00; font-weight: bold')
      error.value = null
    }
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        console.log('WebSocket message received:', {
          type: 'characters update',
          count: data.characters?.length || 0,
          timestamp: new Date().toISOString()
        })
        if (data.characters) {
          characters.value = data.characters
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err)
      }
    }
    
    ws.onerror = (err) => {
      console.error('%cWebSocket Error ❌', 'color: #ff0000; font-weight: bold', err)
      error.value = 'WebSocket connection error. Auto-generation might not work.'
    }
    
    ws.onclose = (event) => {
      console.log('%cWebSocket Closed', 'color: #ffa500; font-weight: bold', {
        code: event.code,
        reason: event.reason,
        wasClean: event.wasClean,
        timestamp: new Date().toISOString()
      })
      if (isAutoGenerating.value) {
        console.log('Auto-generation was active, stopping...')
        stopAutoGenerate()
      }
      // Try to reconnect after a delay if it wasn't a normal closure
      if (event.code !== 1000) {
        console.log('Attempting to reconnect in 5 seconds...')
        setTimeout(setupWebSocket, 5000)
      }
    }
  } catch (err) {
    console.error('Failed to setup WebSocket:', err)
    error.value = 'Failed to connect to server. Please refresh the page.'
  }
}

// Start/Stop auto-generation
const startAutoGenerate = () => {
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    console.error('Cannot start generation - WebSocket not connected')
    error.value = 'WebSocket connection not available. Please refresh the page.'
    return
  }
  
  try {
    console.log('Starting auto-generation...')
    isAutoGenerating.value = true
    ws.send(JSON.stringify({ action: 'start_generation' }))
    error.value = null
  } catch (err) {
    console.error('Failed to start generation:', err)
    error.value = 'Failed to start auto-generation. Please try again.'
    isAutoGenerating.value = false
  }
}

const stopAutoGenerate = () => {
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    console.log('WebSocket not connected, forcing auto-generation stop')
    isAutoGenerating.value = false
    return
  }
  
  try {
    console.log('Stopping auto-generation...')
    ws.send(JSON.stringify({ action: 'stop_generation' }))
    isAutoGenerating.value = false
    error.value = null
  } catch (err) {
    console.error('Failed to stop generation:', err)
    error.value = 'Failed to stop auto-generation, but it will stop soon.'
  }
}

// Load characters and setup WebSocket on mount
onMounted(async () => {
  console.log('Component mounted, initializing...')
  try {
    isLoading.value = true
    error.value = null
    console.log('Fetching initial characters...')
    characters.value = await CharacterService.getAll()
    console.log(`Loaded ${characters.value.length} characters`)
    await setupWebSocket()
  } catch (err) {
    console.error('Failed to initialize:', err)
    error.value = 'Failed to load characters. Please refresh the page.'
  } finally {
    isLoading.value = false
    console.log('Initialization complete')
  }
})

const newCharacter = ref<Omit<Character, 'id'>>({
  name: '',
  hp: 250,
  damage: 50,
  speed: 30,
  armor: 20,
  imageUrl: '/src/assets/chisu.png'
})

// Add form template
const addFormTemplate = {
  name: '',
  hp: 250,
  damage: 50,
  speed: 30,
  armor: 20,
  imageUrl: '/src/assets/chisu.png'
}

const addCharacter = async () => {
  if (!newCharacter.value.name) {
    alert('Please enter a character name')
    return
  }
  
  try {
    error.value = null
    const characterToCreate = {
      ...newCharacter.value,
      hp: Math.max(1, Number(newCharacter.value.hp) || 250),
      damage: Math.max(1, Number(newCharacter.value.damage) || 50),
      speed: Math.max(1, Number(newCharacter.value.speed) || 30),
      armor: Math.max(0, Number(newCharacter.value.armor) || 20),
      imageUrl: '/src/assets/chisu.png'
    }
    
    const created = await CharacterService.create(characterToCreate)
    characters.value.push(created)
    showAddForm.value = false
    newCharacter.value = { ...addFormTemplate }
  } catch (err) {
    console.error('Failed to create character:', err)
    error.value = 'Failed to create character. Please try again.'
  }
}

const updateCharacter = async (character: Character) => {
  try {
    const updated = await CharacterService.update(character)
    const index = characters.value.findIndex(c => c.id === updated.id)
    if (index !== -1) {
      characters.value[index] = updated
    }
    selectedCharacter.value = null
    isEditing.value = false
  } catch (error) {
    console.error('Failed to update character:', error)
  }
}

const deleteCharacter = async (character: Character) => {
  try {
    await CharacterService.delete(character.id)
    characters.value = characters.value.filter(c => c.id !== character.id)
    if (selectedCharacter.value?.id === character.id) {
      selectedCharacter.value = null
    }
  } catch (error) {
    console.error('Failed to delete character:', error)
  }
}

// Character generation function
const generateCharacter = (id: number): Omit<Character, 'id'> => {
  const prefixes = ["Brave", "Swift", "Mighty", "Wise", "Shadow", "Storm", "Iron", "Fire", "Frost", "Thunder"]
  const suffixes = ["walker", "blade", "heart", "soul", "fist", "shield", "master", "slayer", "hunter", "sage"]
  
  const randomPrefix = prefixes[Math.floor(Math.random() * prefixes.length)]
  const randomSuffix = suffixes[Math.floor(Math.random() * suffixes.length)]
  
  return {
    name: `${randomPrefix} ${randomSuffix}`,
    hp: Math.floor(Math.random() * (400 - 250 + 1)) + 250,
    damage: Math.floor(Math.random() * (150 - 50 + 1)) + 50,
    speed: Math.floor(Math.random() * (100 - 30 + 1)) + 30,
    armor: Math.floor(Math.random() * (150 - 20 + 1)) + 20,
    imageUrl: '/src/assets/chisu.png'
  }
}

const generateHundred = async () => {
  try {
    for (let i = 0; i < 100; i++) {
      const newChar = generateCharacter(0)
      const created = await CharacterService.create(newChar)
      characters.value.push(created)
    }
  } catch (error) {
    console.error('Failed to generate characters:', error)
  }
}

const calculateStatsDistribution = computed(() => {
  if (characters.value.length === 0) return null
  
  // Random scaling function that keeps values between 1-100
  const randomScale = (value: number) => {
    // Add some randomness while keeping proportions somewhat meaningful
    const randomFactor = 0.5 + Math.random()
    return Math.min(100, Math.max(1, Math.round(value * randomFactor)))
  }

  const scaledStats = characters.value.reduce((acc, char) => {
    return {
      hp: acc.hp + randomScale(char.hp / 20),      // Divide by 20 to bring 2000 down to 100 range
      damage: acc.damage + randomScale(char.damage / 2),  // Divide by 2 to bring 200 down to 100 range
      speed: acc.speed + randomScale(char.speed),    // Already in good range
      armor: acc.armor + randomScale(char.armor)     // Already in good range
    }
  }, { hp: 0, damage: 0, speed: 0, armor: 0 })
  
  const total = scaledStats.hp + scaledStats.damage + scaledStats.speed + scaledStats.armor
  
  return {
    labels: ['HP', 'Damage', 'Speed', 'Armor'],
    datasets: [{
      data: [
       +(scaledStats.hp / total * 100).toFixed(2),
       +(scaledStats.damage / total * 100).toFixed(2),
       +(scaledStats.speed / total * 100).toFixed(2),
       +(scaledStats.armor / total * 100).toFixed(2)
      ],
      backgroundColor: [
        '#FF6384',
        '#36A2EB',
        '#FFCE56',
        '#4BC0C0'
      ]
    }]
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom' as const,
      labels: {
        color: '#7ee7ff'
      }
    },
    tooltip: {
      callbacks: {
        label: (context: any) => `${context.label}: ${context.raw}%`
      }
    }
  }
}

const selectCharacter = (character: Character) => {
  selectedCharacter.value = character
  showAddForm.value = false
  isEditing.value = false
}

const closeDetail = () => {
  selectedCharacter.value = null
  isEditing.value = false
}

const startEditing = () => {
  if (selectedCharacter.value) {
    isEditing.value = true
  }
}

const cancelEditing = () => {
  isEditing.value = false
}

const saveEdit = () => {
  if (selectedCharacter.value) {
    updateCharacter(selectedCharacter.value)
  }
  isEditing.value = false
}

const toggleAddForm = () => {
  showAddForm.value = !showAddForm.value
  selectedCharacter.value = null
}

// Cleanup on unmount
onUnmounted(() => {
  console.log('Component unmounting, cleaning up...')
  if (ws) {
    isAutoGenerating.value = false
    ws.close(1000, 'Component unmounting')
  }
})
</script>

<template>
  <div class="app">
    <h1>MMO RPG Characters</h1>
    
    <div v-if="error" class="error-message">
      {{ error }}
    </div>
    
    <div v-if="isLoading" class="loading">
      Loading characters...
    </div>
    
    <div v-else class="content-wrapper">
      <div class="content" :class="{ 'with-detail': selectedCharacter || showAddForm }">
        <div class="character-list-container">
          <div class="button-group">
            <button class="add-button" @click="toggleAddForm">
              {{ showAddForm ? 'Cancel' : 'Add New Character' }}
            </button>
            <button class="generate-button" @click="generateHundred">
              Generate 100
            </button>
            <button 
              class="auto-generate-button" 
              @click="isAutoGenerating ? stopAutoGenerate() : startAutoGenerate()"
              :class="{ 'active': isAutoGenerating }"
            >
              {{ isAutoGenerating ? 'Stop Auto Generate' : 'Start Auto Generate' }}
            </button>
          </div>
          
          <!-- Stats Distribution Chart -->
          <div v-if="characters.length > 0" class="chart-container">
            <h3>Stats Distribution</h3>
            <Pie
              v-if="calculateStatsDistribution"
              :data="calculateStatsDistribution"
              :options="chartOptions"
            />
          </div>

          <div class="character-list">
            <div 
              v-for="character in characters" 
              :key="character.id"
              class="character-card"
              :class="{ 'selected': selectedCharacter?.id === character.id }"
              @click="selectCharacter(character)"
            >
              <h3>{{ character.name }}</h3>
              <div class="stats-preview">
                <div>HP: {{ character.hp }}</div>
                <div>DMG: {{ character.damage }}</div>
              </div>
              <button 
                class="delete-button" 
                @click.stop="deleteCharacter(character)"
                title="Delete Character"
              >×</button>
            </div>
          </div>
        </div>

        <!-- Add Character Form -->
        <div v-if="showAddForm" class="character-form">
          <h3>Add New Character</h3>
          <form @submit.prevent="addCharacter">
            <div class="form-group">
              <label>Name:</label>
              <input v-model="newCharacter.name" required>
            </div>
            <div class="form-group">
              <label>HP:</label>
              <input 
                type="number" 
                v-model.number="newCharacter.hp" 
                required 
                min="1"
                :placeholder="addFormTemplate.hp.toString()"
              >
            </div>
            <div class="form-group">
              <label>Damage:</label>
              <input 
                type="number" 
                v-model.number="newCharacter.damage" 
                required 
                min="1"
                :placeholder="addFormTemplate.damage.toString()"
              >
            </div>
            <div class="form-group">
              <label>Speed:</label>
              <input 
                type="number" 
                v-model.number="newCharacter.speed" 
                required 
                min="1"
                :placeholder="addFormTemplate.speed.toString()"
              >
            </div>
            <div class="form-group">
              <label>Armor:</label>
              <input 
                type="number" 
                v-model.number="newCharacter.armor" 
                required 
                min="0"
                :placeholder="addFormTemplate.armor.toString()"
              >
            </div>
            <div class="form-buttons">
              <button type="submit" class="save-button">Add Character</button>
              <button type="button" class="cancel-button" @click="showAddForm = false">Cancel</button>
            </div>
          </form>
        </div>

        <!-- Character Detail -->
        <div v-if="selectedCharacter" class="character-detail">
          <button class="close-button" @click="closeDetail">×</button>
          
          <!-- View Mode -->
          <div v-if="!isEditing">
            <div class="detail-header">
              <img :src="selectedCharacter.imageUrl" :alt="selectedCharacter.name">
              <div class="character-info">
                <h2>{{ selectedCharacter.name }}</h2>
                <div class="id-display">ID: {{ selectedCharacter.id }}</div>
              </div>
            </div>

            <div class="stats-grid">
              <div class="stat-item">
                <span class="stat-label">HP</span>
                <span class="stat-value">{{ selectedCharacter.hp }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">Damage</span>
                <span class="stat-value">{{ selectedCharacter.damage }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">Speed</span>
                <span class="stat-value">{{ selectedCharacter.speed }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">Armor</span>
                <span class="stat-value">{{ selectedCharacter.armor }}</span>
              </div>
            </div>

            <div class="action-buttons">
              <button class="edit-button" @click="startEditing">Edit Character</button>
              <button class="delete-button-large" @click="deleteCharacter(selectedCharacter)">
                Delete Character
              </button>
            </div>
          </div>

          <!-- Edit Mode -->
          <div v-else class="edit-mode">
            <h2>Edit Character</h2>
            <form @submit.prevent="saveEdit">
              <div class="form-group">
                <label>Name:</label>
                <input v-model="selectedCharacter.name" required>
              </div>
              <div class="form-group">
                <label>HP:</label>
                <input type="number" v-model="selectedCharacter.hp" required min="1">
              </div>
              <div class="form-group">
                <label>Damage:</label>
                <input type="number" v-model="selectedCharacter.damage" required min="0">
              </div>
              <div class="form-group">
                <label>Speed:</label>
                <input type="number" v-model="selectedCharacter.speed" required min="1">
              </div>
              <div class="form-group">
                <label>Armor:</label>
                <input type="number" v-model="selectedCharacter.armor" required min="0">
              </div>
              <div class="edit-buttons">
                <button type="submit" class="save-button">Save Changes</button>
                <button type="button" class="cancel-button" @click="cancelEditing">Cancel</button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.app {
  width: 100%;
  min-height: 100vh;
  background: linear-gradient(135deg, #1a1c2c 0%, #2a3c54 100%);
  color: #ffffff;
}

h1 {
  color: #7ee7ff;
  text-align: center;
  margin: 0;
  padding: 2rem 0;
  text-shadow: 0 0 10px rgba(126, 231, 255, 0.5);
}

.content-wrapper {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
  display: flex;
  justify-content: center;
}

.content {
  display: flex;
  gap: 2rem;
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
}

.character-list-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  width: 500px;
}

.button-group {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.add-button {
  background: #7ee7ff;
  color: #1a1c2c;
  border: none;
  padding: 0.8rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: bold;
  transition: all 0.3s ease;
  flex: 1;
}

.add-button:hover {
  background: #5cd9ff;
  transform: translateY(-2px);
}

.generate-button {
  background: #ff9d00;
  color: #1a1c2c;
  border: none;
  padding: 0.8rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: bold;
  transition: all 0.3s ease;
  flex: 1;
}

.generate-button:hover {
  background: #ffb340;
  transform: translateY(-2px);
}

.auto-generate-button {
  background: #2c3e50;
  color: #7ee7ff;
  border: 2px solid #7ee7ff;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
}

.auto-generate-button.active {
  background: #7ee7ff;
  color: #2c3e50;
}

.auto-generate-button.active::after {
  content: '';
  position: absolute;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ff4757;
  top: -4px;
  right: -4px;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.2);
    opacity: 0.8;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

.character-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
  width: 500px;
}

.character-card {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  padding: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  width: 100%;
  position: relative;
}

.character-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(126, 231, 255, 0.3);
  border-color: #7ee7ff;
}

.character-card.selected {
  border-color: #7ee7ff;
  background: rgba(126, 231, 255, 0.1);
  box-shadow: 0 0 20px rgba(126, 231, 255, 0.2);
}

.character-brief {
  display: flex;
  justify-content: space-between;
  margin: 0.5rem 0;
  font-size: 0.9rem;
  color: #a8d8e8;
}

.stats-preview {
  display: flex;
  justify-content: space-between;
  margin-top: 0.5rem;
  font-size: 0.9rem;
  color: #7ee7ff;
}

.delete-button {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  background: rgba(255, 99, 99, 0.2);
  border: none;
  width: 24px;
  height: 24px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ff6363;
  cursor: pointer;
  font-size: 1.2rem;
  opacity: 0;
  transition: all 0.3s ease;
}

.character-card:hover .delete-button {
  opacity: 1;
}

.delete-button:hover {
  background: rgba(255, 99, 99, 0.4);
  transform: scale(1.1);
}

.delete-button-large {
  background: rgba(255, 99, 99, 0.2);
  color: #ff6363;
  border: none;
  padding: 0.8rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  margin-top: 2rem;
  width: 100%;
  font-weight: bold;
  transition: all 0.3s ease;
}

.delete-button-large:hover {
  background: rgba(255, 99, 99, 0.4);
}

.character-form {
  width: 500px;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: #7ee7ff;
}

.form-group input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid rgba(126, 231, 255, 0.5);
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.1);
  color: #7ee7ff;
  margin-top: 0.25rem;
}

.form-group input::placeholder {
  color: rgba(126, 231, 255, 0.5);
}

.form-group input:focus {
  outline: none;
  border-color: #7ee7ff;
  box-shadow: 0 0 0 2px rgba(126, 231, 255, 0.2);
}

.form-buttons {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
}

.save-button, .cancel-button {
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.save-button {
  background: #7ee7ff;
  color: #2c3e50;
  border: none;
}

.cancel-button {
  background: transparent;
  color: #7ee7ff;
  border: 1px solid #7ee7ff;
}

.save-button:hover {
  background: #5cd9ff;
}

.cancel-button:hover {
  background: rgba(126, 231, 255, 0.1);
}

.character-detail {
  width: 500px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 2rem;
  position: relative;
  box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
}

.close-button {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: none;
  border: none;
  font-size: 2rem;
  cursor: pointer;
  color: #7ee7ff;
  text-shadow: 0 0 10px rgba(126, 231, 255, 0.5);
}

.detail-header {
  display: flex;
  gap: 2rem;
  margin-bottom: 2rem;
}

.detail-header img {
  width: 200px;
  height: 200px;
  border-radius: 8px;
  object-fit: cover;
  border: 2px solid #7ee7ff;
  box-shadow: 0 0 20px rgba(126, 231, 255, 0.2);
}

.character-info {
  flex: 1;
}

.id-display {
  color: #7ee7ff;
  font-size: 0.9rem;
  margin-top: 0.5rem;
  opacity: 0.8;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin-top: 2rem;
}

.stat-item {
  background: rgba(255, 255, 255, 0.05);
  padding: 1rem;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  align-items: center;
  border: 1px solid rgba(126, 231, 255, 0.2);
}

.stat-label {
  font-size: 0.9rem;
  color: #a8d8e8;
  margin-bottom: 0.3rem;
}

.stat-value {
  font-size: 1.2rem;
  font-weight: bold;
  color: #7ee7ff;
  text-shadow: 0 0 10px rgba(126, 231, 255, 0.3);
}

.action-buttons {
  display: flex;
  gap: 1rem;
  margin-top: 2rem;
}

.edit-button {
  flex: 1;
  background: rgba(126, 231, 255, 0.2);
  color: #7ee7ff;
  border: none;
  padding: 0.8rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: bold;
  transition: all 0.3s ease;
}

.edit-button:hover {
  background: rgba(126, 231, 255, 0.4);
}

.delete-button-large {
  flex: 1;
}

.edit-mode {
  padding: 1rem 0;
}

.edit-buttons {
    display: flex;
  gap: 1rem;
  margin-top: 1rem;
}

.save-button {
  flex: 1;
  background: #7ee7ff;
  color: #1a1c2c;
  border: none;
  padding: 0.8rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: bold;
  transition: all 0.3s ease;
}

.save-button:hover {
  background: #5cd9ff;
  transform: translateY(-2px);
}

.cancel-button {
  flex: 1;
  background: rgba(255, 99, 99, 0.2);
  color: #ff6363;
  border: none;
  padding: 0.8rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: bold;
  transition: all 0.3s ease;
}

.cancel-button:hover {
  background: rgba(255, 99, 99, 0.4);
}

@media (max-width: 768px) {
  .content {
    flex-direction: column;
    align-items: center;
  }

  .character-list {
    width: 100%;
    max-width: 300px;
  }

  .character-detail {
    width: 100%;
    max-width: 500px;
    margin-top: 2rem;
  }

  .detail-header {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
}

.chart-container {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
  height: 300px;
}

.chart-container h3 {
  color: #7ee7ff;
  text-align: center;
  margin-bottom: 1rem;
}

.error-message {
  background: rgba(255, 0, 0, 0.1);
  border: 1px solid rgba(255, 0, 0, 0.3);
  color: #ff6b6b;
  padding: 1rem;
  margin: 1rem 0;
  border-radius: 4px;
  text-align: center;
}

.loading {
  color: #7ee7ff;
  text-align: center;
  padding: 2rem;
  font-size: 1.2rem;
}
</style>
