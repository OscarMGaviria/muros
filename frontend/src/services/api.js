import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const calculateWallDesign = async (payload) => {
  try {
    const response = await axios.post(`${API_URL}/api/v1/design/ccp14`, payload)
    return response.data
  } catch (error) {
    console.error("Error en el cálculo:", error)
    throw error
  }
}

export const checkServerHealth = async () => {
  try {
    await axios.get(`${API_URL}/health`, { timeout: 3000 })
    return true
  } catch (error) {
    return false
  }
}
