import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface User {
  id: number
  email: string
  username: string | null
  full_name: string | null
  profile_picture: string | null
  auth_provider: string
  is_verified: boolean
  storage_used: number
  reports_generated: number
  created_at: string
}

interface AuthState {
  // Auth state
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  _hasHydrated: boolean
  
  // Actions
  login: (accessToken: string, refreshToken: string, user: User) => void
  logout: () => void
  updateUser: (user: User) => void
  setTokens: (accessToken: string, refreshToken?: string) => void
  setHasHydrated: (state: boolean) => void
}

// Selector for isAuthenticated (computed from state)
export const selectIsAuthenticated = (state: AuthState): boolean => {
  return !!(state.accessToken && state.user)
}

const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      // Initial state
      user: null,
      accessToken: null,
      refreshToken: null,
      _hasHydrated: false,

      // Login action
      login: (accessToken, refreshToken, user) => {
        console.log('Setting auth state:', { accessToken: accessToken?.substring(0, 20), refreshToken: refreshToken?.substring(0, 20), user: user?.email })
        set({
          accessToken,
          refreshToken,
          user,
        })
        // Verify state was set
        const state = useAuthStore.getState()
        const isAuth = selectIsAuthenticated(state)
        console.log('Auth state after set:', { 
          isAuthenticated: isAuth, 
          hasToken: !!state.accessToken, 
          hasUser: !!state.user 
        })
      },

      // Logout action
      logout: () => {
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
        })
      },

      // Update user info
      updateUser: (user) => {
        set({ user })
      },

      // Set tokens (for token refresh)
      setTokens: (accessToken, refreshToken) => {
        set((state) => ({
          accessToken,
          refreshToken: refreshToken || state.refreshToken,
        }))
      },

      // Set hydration state
      setHasHydrated: (state) => {
        set({ _hasHydrated: state })
      },
    }),
    {
      name: 'auth-storage', // localStorage key
      partialize: (state) => ({
        // Only persist tokens and user, not isAuthenticated (derived) or _hasHydrated
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
      }),
      onRehydrateStorage: () => (state) => {
        // Called after rehydration completes
        if (state) {
          state.setHasHydrated(true)
        }
      },
    }
  )
)

export { useAuthStore }

