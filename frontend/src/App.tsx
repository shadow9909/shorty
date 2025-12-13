import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'

function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center p-8">
      <div className="bg-white/90 backdrop-blur-xl shadow-2xl rounded-3xl p-12 max-w-md w-full mx-4 border border-white/20">
        <h1 className="text-4xl font-black bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent mb-8 text-center">
          Vite + React + Tailwind
        </h1>
        <div className="space-y-4">
          <button className="w-full bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white font-bold py-4 px-8 rounded-2xl transition-all duration-300 transform hover:scale-105 hover:shadow-xl active:scale-95">
            🚀 Get Started
          </button>
          <p className="text-center text-gray-600 text-lg italic">
            Lightning fast HMR + Full TypeScript
          </p>
        </div>
      </div>
    </div>
  )
}


export default App
