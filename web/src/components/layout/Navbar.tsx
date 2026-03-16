import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useState, useRef, useEffect } from 'react'
import { UserCircle, LogOut, FileText, ChevronDown } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { logout } from '@/services/api'
import toast from 'react-hot-toast'

export default function Navbar() {
  const location = useLocation()
  const navigate = useNavigate()
  const authState = useAuthStore()
  const isAuthenticated = !!(authState.accessToken && authState.user)
  const { user, logout: logoutStore } = authState
  const [showUserMenu, setShowUserMenu] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)
  
  const isActive = (path: string) => location.pathname === path

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setShowUserMenu(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleLogout = async () => {
    try {
      await logout()
      logoutStore()
      toast.success('Logged out successfully')
      navigate('/')
    } catch (error) {
      // Even if API call fails, clear local state
      logoutStore()
      toast.success('Logged out')
      navigate('/')
    }
    setShowUserMenu(false)
  }

  const getUserDisplayName = () => {
    if (user?.full_name) return user.full_name
    if (user?.username) return user.username
    return user?.email?.split('@')[0] || 'User'
  }

  return (
    <nav className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-sm sticky top-0 z-50">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 group">
            <div className="flex gap-1">
              {[...Array(4)].map((_, i) => (
                <div
                  key={i}
                  className="w-2 h-2 bg-primary-500 rounded-full group-hover:bg-primary-400 transition-colors"
                  style={{ animationDelay: `${i * 0.1}s` }}
                />
              ))}
            </div>
            <span className="text-xl font-bold gradient-text">ReportForge AI</span>
          </Link>
          
          <div className="flex items-center gap-6">
            <Link
              to="/"
              className={`px-3 py-2 rounded-lg transition-colors ${
                isActive('/') 
                  ? 'bg-primary-600 text-white' 
                  : 'text-text-secondary hover:text-text-primary hover:bg-slate-800'
              }`}
            >
              Home
            </Link>
            
            {isAuthenticated ? (
              <>
                <Link
                  to="/dashboard"
                  className={`px-3 py-2 rounded-lg transition-colors ${
                    isActive('/dashboard') 
                      ? 'bg-primary-600 text-white' 
                      : 'text-text-secondary hover:text-text-primary hover:bg-slate-800'
                  }`}
                >
                  Dashboard
                </Link>
                <Link
                  to="/upload"
                  className={`px-3 py-2 rounded-lg transition-colors ${
                    isActive('/upload') 
                      ? 'bg-primary-600 text-white' 
                      : 'text-text-secondary hover:text-text-primary hover:bg-slate-800'
                  }`}
                >
                  Generate Report
                </Link>
                <Link
                  to="/history"
                  className={`px-3 py-2 rounded-lg transition-colors ${
                    isActive('/history') 
                      ? 'bg-primary-600 text-white' 
                      : 'text-text-secondary hover:text-text-primary hover:bg-slate-800'
                  }`}
                >
                  History
                </Link>
                
                {/* User Menu */}
                <div className="relative" ref={menuRef}>
                  <button
                    onClick={() => setShowUserMenu(!showUserMenu)}
                    className="flex items-center gap-2 px-3 py-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-slate-800 transition-colors"
                  >
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-accent-purple flex items-center justify-center text-white text-sm font-semibold">
                      {user?.full_name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || 'U'}
                    </div>
                    <span className="hidden md:block">{getUserDisplayName()}</span>
                    <ChevronDown className={`w-4 h-4 transition-transform ${showUserMenu ? 'rotate-180' : ''}`} />
                  </button>
                  
                  {/* Dropdown Menu */}
                  {showUserMenu && (
                    <div className="absolute right-0 mt-2 w-56 glass-card rounded-lg shadow-xl border border-slate-700 overflow-hidden">
                      <div className="p-4 border-b border-slate-700">
                        <p className="text-sm font-semibold text-text-primary">{getUserDisplayName()}</p>
                        <p className="text-xs text-text-muted mt-1">{user?.email}</p>
                      </div>
                      
                      <div className="py-2">
                        <Link
                          to="/history"
                          onClick={() => setShowUserMenu(false)}
                          className="flex items-center gap-3 px-4 py-2 text-sm text-text-secondary hover:text-text-primary hover:bg-slate-800 transition-colors"
                        >
                          <FileText className="w-4 h-4" />
                          My Reports
                        </Link>
                        <Link
                          to="/profile"
                          onClick={() => setShowUserMenu(false)}
                          className="flex items-center gap-3 px-4 py-2 text-sm text-text-secondary hover:text-text-primary hover:bg-slate-800 transition-colors"
                        >
                          <UserCircle className="w-4 h-4" />
                          Profile & Settings
                        </Link>
                        <button
                          onClick={handleLogout}
                          className="w-full flex items-center gap-3 px-4 py-2 text-sm text-text-secondary hover:text-red-400 hover:bg-slate-800 transition-colors"
                        >
                          <LogOut className="w-4 h-4" />
                          Sign Out
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <>
                <Link
                  to="/login"
                  className="px-3 py-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-slate-800 transition-colors"
                >
                  Sign In
                </Link>
                <Link
                  to="/register"
                  className="px-4 py-2 rounded-lg gradient-button text-white"
                >
                  Sign Up
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}
