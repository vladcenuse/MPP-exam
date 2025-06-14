const API_URL = 'http://localhost:8000'

export interface Character {
    id: number
    name: string
    hp: number
    damage: number
    speed: number
    armor: number
    imageUrl: string
}

export const CharacterService = {
    async getAll(): Promise<Character[]> {
        const response = await fetch(`${API_URL}/characters`)
        if (!response.ok) {
            throw new Error(`Failed to fetch characters: ${response.statusText}`)
        }
        const data = await response.json()
        return data
    },

    async create(character: Omit<Character, 'id'>): Promise<Character> {
        const response = await fetch(`${API_URL}/characters`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                id: 0, // This will be ignored/overwritten by the backend
                ...character
            }),
        })
        if (!response.ok) {
            throw new Error(`Failed to create character: ${response.statusText}`)
        }
        const data = await response.json()
        return data
    },

    async update(character: Character): Promise<Character> {
        const response = await fetch(`${API_URL}/characters/${character.id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(character),
        })
        if (!response.ok) {
            throw new Error(`Failed to update character: ${response.statusText}`)
        }
        const data = await response.json()
        return data
    },

    async delete(id: number): Promise<void> {
        const response = await fetch(`${API_URL}/characters/${id}`, {
            method: 'DELETE',
        })
        if (!response.ok) {
            throw new Error(`Failed to delete character: ${response.statusText}`)
        }
    }
} 