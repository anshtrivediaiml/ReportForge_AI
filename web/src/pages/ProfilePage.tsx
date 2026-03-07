import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { User, Mail, Lock, HardDrive, FileText, Settings, Save, Eye, EyeOff, Loader2, AlertTriangle, Trash2 } from 'lucide-react'
import Button from '@/components/common/Button'
import Card from '@/components/common/Card'
import { useAuthStore } from '@/store/authStore'
import { updateProfile, changePassword, getUserStats, getCurrentUser, deleteAccount } from '@/services/api'
import { formatBytes } from '@/utils/formatters'
import toast from 'react-hot-toast'
import { SkeletonCard } from '@/components/common/Skeleton'
import ConfirmDialog from '@/components/common/ConfirmDialog'

export default function ProfilePage() {
  const navigate = useNavigate()
  const { user, updateUser, logout } = useAuthStore()
  const [loading, setLoading] = useState(false) // Start with false - we have user from store
  const [stats, setStats] = useState<any>(null)
  const [activeTab, setActiveTab] = useState<'profile' | 'password' | 'account'>('profile')
  
  // Profile form state - initialize from user immediately
  const [fullName, setFullName] = useState(user?.full_name || '')
  const [username, setUsername] = useState(user?.username || '')
  const [savingProfile, setSavingProfile] = useState(false)
  
  // Password form state
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showCurrentPassword, setShowCurrentPassword] = useState(false)
  const [showNewPassword, setShowNewPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [savingPassword, setSavingPassword] = useState(false)
  
  // Security/Danger zone state
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [deleteConfirmText, setDeleteConfirmText] = useState('')
  const [deletingAccount, setDeletingAccount] = useState(false)
  
  // Password validation helpers
  const getPasswordRequirements = () => {
    return {
      minLength: newPassword.length >= 8,
      hasUppercase: /[A-Z]/.test(newPassword),
      hasLowercase: /[a-z]/.test(newPassword),
      hasDigit: /[0-9]/.test(newPassword),
      hasSpecialChar: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(newPassword),
      passwordsMatch: newPassword === confirmPassword && confirmPassword.length > 0
    }
  }

  useEffect(() => {
    if (!user) {
      navigate('/login')
      return
    }
    
    // Initialize form fields from user data
    setFullName(user.full_name || '')
    setUsername(user.username || '')
    
    const fetchData = async () => {
      setLoading(true)
      
      // Set a timeout to ensure loading doesn't hang forever
      const timeoutId = setTimeout(() => {
        console.warn('Profile data fetch timeout, using cached data')
        setLoading(false)
      }, 3000) // 3 second timeout
      
      try {
        // Try to fetch fresh data - use allSettled so one failure doesn't break everything
        const [userData, userStats] = await Promise.allSettled([
          getCurrentUser().catch(err => {
            console.warn('getCurrentUser error:', err)
            return null
          }),
          getUserStats().catch(err => {
            console.warn('getUserStats error:', err)
            return null
          })
        ])
        
        clearTimeout(timeoutId)
        
        // Handle user data
        if (userData.status === 'fulfilled' && userData.value) {
          updateUser(userData.value)
          setFullName(userData.value.full_name || '')
          setUsername(userData.value.username || '')
        }
        
        // Handle stats
        if (userStats.status === 'fulfilled' && userStats.value) {
          setStats(userStats.value)
        }
      } catch (error: any) {
        clearTimeout(timeoutId)
        console.error('Error in fetchData:', error)
      } finally {
        setLoading(false)
      }
    }
    
    // Only fetch if we don't have stats yet
    if (!stats) {
      fetchData()
    }
  }, [user, navigate, updateUser]) // Include user in deps to update when user changes

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault()
    setSavingProfile(true)
    try {
      const updatedUser = await updateProfile({ full_name: fullName, username: username || undefined })
      updateUser(updatedUser)
      toast.success('Profile updated successfully!')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to update profile')
    } finally {
      setSavingProfile(false)
    }
  }

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Password validation
    const requirements = getPasswordRequirements()
    
    if (!requirements.minLength) {
      toast.error('Password must be at least 8 characters long')
      return
    }
    
    if (!requirements.hasUppercase) {
      toast.error('Password must contain at least one uppercase letter')
      return
    }
    
    if (!requirements.hasLowercase) {
      toast.error('Password must contain at least one lowercase letter')
      return
    }
    
    if (!requirements.hasDigit) {
      toast.error('Password must contain at least one digit (0-9)')
      return
    }
    
    if (!requirements.hasSpecialChar) {
      toast.error('Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)')
      return
    }

    if (!requirements.passwordsMatch) {
      toast.error('New passwords do not match')
      return
    }
    
    setSavingPassword(true)
    try {
      await changePassword({ current_password: currentPassword, new_password: newPassword })
      toast.success('Password changed successfully!')
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to change password')
    } finally {
      setSavingPassword(false)
    }
  }

  // Redirect if no user
  if (!user) {
    return null
  }

  // Show loading skeleton only if we're loading AND don't have user data yet
  // But since we have user from store, we should show content immediately
  if (loading && !user) {
    return (
      <div className="container mx-auto px-6 py-12 max-w-4xl">
        <SkeletonCard />
      </div>
    )
  }

  const isEmailUser = user.auth_provider === 'email'

  return (
    <div className="container mx-auto px-6 py-12 max-w-4xl">
      <h1 className="text-4xl font-bold gradient-text mb-8">Profile & Settings</h1>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar */}
        <div className="lg:col-span-1">
          <Card className="p-4">
            <nav className="space-y-2">
              <button
                onClick={() => setActiveTab('profile')}
                className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
                  activeTab === 'profile'
                    ? 'bg-primary-600 text-white'
                    : 'text-text-secondary hover:bg-slate-800 hover:text-text-primary'
                }`}
              >
                <User className="w-4 h-4 inline mr-2" />
                Profile
              </button>
              {isEmailUser && (
                <button
                  onClick={() => setActiveTab('password')}
                  className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
                    activeTab === 'password'
                      ? 'bg-primary-600 text-white'
                      : 'text-text-secondary hover:bg-slate-800 hover:text-text-primary'
                  }`}
                >
                  <Lock className="w-4 h-4 inline mr-2" />
                  Password
                </button>
              )}
              <button
                onClick={() => setActiveTab('account')}
                className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
                  activeTab === 'account'
                    ? 'bg-primary-600 text-white'
                    : 'text-text-secondary hover:bg-slate-800 hover:text-text-primary'
                }`}
              >
                <Settings className="w-4 h-4 inline mr-2" />
                Account
              </button>
            </nav>
          </Card>
        </div>

        {/* Main Content */}
        <div className="lg:col-span-3">
          {/* Profile Tab */}
          {activeTab === 'profile' && (
            <Card className="p-6">
              <h2 className="text-2xl font-bold text-text-primary mb-6">Profile Information</h2>
              <form onSubmit={handleUpdateProfile} className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">
                    Email Address
                  </label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                    <input
                      type="email"
                      className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg"
                      value={user.email}
                      disabled
                    />
                  </div>
                  <p className="text-xs text-text-muted mt-1">Email cannot be changed</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">
                    Full Name
                  </label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                    <input
                      type="text"
                      className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg focus:ring-primary-500 focus:border-primary-500"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="Your full name"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">
                    Username (Optional)
                  </label>
                  <input
                    type="text"
                    className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg focus:ring-primary-500 focus:border-primary-500"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="username"
                  />
                </div>

                <Button type="submit" disabled={savingProfile}>
                  {savingProfile ? <Loader2 className="w-5 h-5 animate-spin mr-2" /> : <Save className="w-5 h-5 mr-2" />}
                  Save Changes
                </Button>
              </form>
            </Card>
          )}

          {/* Password Tab (Email users only) */}
          {activeTab === 'password' && isEmailUser && (
            <Card className="p-6">
              <h2 className="text-2xl font-bold text-text-primary mb-6">Change Password</h2>
              <form onSubmit={handleChangePassword} className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">
                    Current Password
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                    <input
                      type={showCurrentPassword ? 'text' : 'password'}
                      className="w-full pl-10 pr-10 py-2 bg-slate-800 border border-slate-700 rounded-lg focus:ring-primary-500 focus:border-primary-500"
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-text-primary"
                    >
                      {showCurrentPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">
                    New Password
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                    <input
                      type={showNewPassword ? 'text' : 'password'}
                      className="w-full pl-10 pr-10 py-2 bg-slate-800 border border-slate-700 rounded-lg focus:ring-primary-500 focus:border-primary-500"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      required
                      minLength={8}
                    />
                    <button
                      type="button"
                      onClick={() => setShowNewPassword(!showNewPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-text-primary"
                    >
                      {showNewPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                  {/* Password Requirements */}
                  {newPassword && (
                    <div className="mt-2 space-y-1">
                      <p className="text-xs font-medium text-text-secondary mb-2">Password requirements:</p>
                      <div className="space-y-1">
                        <div className={`text-xs flex items-center gap-2 ${getPasswordRequirements().minLength ? 'text-green-400' : 'text-text-muted'}`}>
                          <span>{getPasswordRequirements().minLength ? '[OK]' : '[ ]'}</span>
                          <span>At least 8 characters</span>
                        </div>
                        <div className={`text-xs flex items-center gap-2 ${getPasswordRequirements().hasUppercase ? 'text-green-400' : 'text-text-muted'}`}>
                          <span>{getPasswordRequirements().hasUppercase ? '[OK]' : '[ ]'}</span>
                          <span>One uppercase letter (A-Z)</span>
                        </div>
                        <div className={`text-xs flex items-center gap-2 ${getPasswordRequirements().hasLowercase ? 'text-green-400' : 'text-text-muted'}`}>
                          <span>{getPasswordRequirements().hasLowercase ? '[OK]' : '[ ]'}</span>
                          <span>One lowercase letter (a-z)</span>
                        </div>
                        <div className={`text-xs flex items-center gap-2 ${getPasswordRequirements().hasDigit ? 'text-green-400' : 'text-text-muted'}`}>
                          <span>{getPasswordRequirements().hasDigit ? '[OK]' : '[ ]'}</span>
                          <span>One digit (0-9)</span>
                        </div>
                        <div className={`text-xs flex items-center gap-2 ${getPasswordRequirements().hasSpecialChar ? 'text-green-400' : 'text-text-muted'}`}>
                          <span>{getPasswordRequirements().hasSpecialChar ? '[OK]' : '[ ]'}</span>
                          <span>One special character (!@#$%^&*...)</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">
                    Confirm New Password
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                    <input
                      type={showConfirmPassword ? 'text' : 'password'}
                      className="w-full pl-10 pr-10 py-2 bg-slate-800 border border-slate-700 rounded-lg focus:ring-primary-500 focus:border-primary-500"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      required
                      minLength={8}
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-text-primary"
                    >
                      {showConfirmPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                  {/* Password Match Indicator */}
                  {confirmPassword && (
                    <div className="mt-1">
                      {getPasswordRequirements().passwordsMatch ? (
                        <p className="text-xs text-green-400 flex items-center gap-1">
                          <span>[OK]</span>
                          <span>Passwords match</span>
                        </p>
                      ) : (
                        <p className="text-xs text-red-400 flex items-center gap-1">
                          <span>[X]</span>
                          <span>Passwords do not match</span>
                        </p>
                      )}
                    </div>
                  )}
                </div>

                <Button type="submit" disabled={savingPassword}>
                  {savingPassword ? <Loader2 className="w-5 h-5 animate-spin mr-2" /> : <Save className="w-5 h-5 mr-2" />}
                  Change Password
                </Button>
              </form>
            </Card>
          )}

          {/* Account Tab */}
          {activeTab === 'account' && (
            <div className="space-y-6">
              <Card className="p-6">
                <h2 className="text-2xl font-bold text-text-primary mb-6">Account Information</h2>
                <div className="space-y-4">
                  <div className="flex items-center justify-between py-3 border-b border-slate-700">
                    <div className="flex items-center gap-3">
                      <Mail className="w-5 h-5 text-slate-500" />
                      <span className="text-text-secondary">Email</span>
                    </div>
                    <span className="text-text-primary font-medium">{user.email}</span>
                  </div>
                  <div className="flex items-center justify-between py-3 border-b border-slate-700">
                    <div className="flex items-center gap-3">
                      <Settings className="w-5 h-5 text-slate-500" />
                      <span className="text-text-secondary">Auth Provider</span>
                    </div>
                    <span className="text-text-primary font-medium capitalize">{user.auth_provider}</span>
                  </div>
                  <div className="flex items-center justify-between py-3 border-b border-slate-700">
                    <div className="flex items-center gap-3">
                      <FileText className="w-5 h-5 text-slate-500" />
                      <span className="text-text-secondary">Reports Generated</span>
                    </div>
                    <span className="text-text-primary font-medium">{user.reports_generated}</span>
                  </div>
                </div>
              </Card>

              <Card className="p-6">
                <h2 className="text-2xl font-bold text-text-primary mb-6">Storage Usage</h2>
                {stats ? (
                  <div className="space-y-4">
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-3">
                          <HardDrive className="w-5 h-5 text-accent-cyan" />
                          <span className="text-text-secondary">Storage Used</span>
                        </div>
                        <span className="text-text-primary font-medium">
                          {formatBytes(stats.storage_used)} / {formatBytes(stats.storage_limit)}
                        </span>
                      </div>
                      <div className="w-full bg-slate-700 rounded-full h-3">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${
                            stats.storage_used_percent > 90
                              ? 'bg-red-500'
                              : stats.storage_used_percent > 80
                              ? 'bg-yellow-500'
                              : 'bg-primary-500'
                          }`}
                          style={{ width: `${stats.storage_used_percent}%` }}
                        />
                      </div>
                      <p className="text-sm text-text-muted mt-2">
                        {stats.storage_used_percent.toFixed(2)}% of your storage limit used
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="text-text-muted">
                    <p>Storage information will be available once you generate your first report.</p>
                    <p className="text-sm mt-2">Current storage: {formatBytes(user.storage_used || 0)}</p>
                  </div>
                )}
              </Card>

              {/* Danger Zone */}
              <Card className="p-6 border-red-500/30">
                <div className="flex items-center gap-2 mb-4">
                  <AlertTriangle className="w-5 h-5 text-red-400" />
                  <h2 className="text-2xl font-bold text-red-400">Danger Zone</h2>
                </div>
                <div className="space-y-4">
                  <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
                    <h3 className="font-semibold text-text-primary mb-2">Delete Account</h3>
                    <p className="text-sm text-text-muted mb-4">
                      Once you delete your account, there is no going back. This will permanently delete:
                    </p>
                    <ul className="text-sm text-text-muted list-disc list-inside space-y-1 mb-4">
                      <li>All your reports and generated files</li>
                      <li>Your account data and profile information</li>
                      <li>All associated storage and files</li>
                    </ul>
                    <Button
                      variant="outline"
                      onClick={() => setShowDeleteConfirm(true)}
                      className="border-red-500 text-red-400 hover:bg-red-500/10"
                    >
                      <Trash2 className="w-4 h-4 mr-2" />
                      Delete My Account
                    </Button>
                  </div>
                </div>
              </Card>
            </div>
          )}
        </div>
      </div>

      {/* Delete Account Confirmation Dialog */}
      <ConfirmDialog
        isOpen={showDeleteConfirm}
        onClose={() => {
          setShowDeleteConfirm(false)
          setDeleteConfirmText('')
        }}
        onConfirm={async () => {
          if (deleteConfirmText.toLowerCase() !== 'delete') {
            toast.error('Please type "delete" to confirm')
            return
          }
          
          setDeletingAccount(true)
          try {
            await deleteAccount()
            toast.success('Account deleted successfully')
            setShowDeleteConfirm(false)
            setDeleteConfirmText('')
            // Logout and redirect to home
            logout()
            navigate('/')
          } catch (error: any) {
            toast.error(error.response?.data?.detail || 'Failed to delete account')
          } finally {
            setDeletingAccount(false)
          }
        }}
        title="Delete Account"
        message={
          <div className="space-y-4">
            <p className="text-text-primary">
              Are you absolutely sure you want to delete your account? This action cannot be undone.
            </p>
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-2">
                Type <span className="font-mono text-red-400">delete</span> to confirm:
              </label>
              <input
                type="text"
                value={deleteConfirmText}
                onChange={(e) => setDeleteConfirmText(e.target.value)}
                className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-text-primary focus:ring-red-500 focus:border-red-500"
                placeholder="delete"
                autoFocus
              />
            </div>
          </div>
        }
        confirmText="Delete Account"
        cancelText="Cancel"
        variant="danger"
        loading={deletingAccount}
      />
    </div>
  )
}

