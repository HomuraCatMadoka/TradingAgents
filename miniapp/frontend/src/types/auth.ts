export interface User {
  id: string | number
  username?: string
  firstName?: string
  lastName?: string
  photoUrl?: string
}

export interface Session {
  issuedAt: string
  expiresAt: string
}

export interface AuthTokens {
  accessToken: string
  refreshToken: string
}

export interface AuthResponse {
  user: User
  session?: Session | null
  token?: string
  accessToken?: string
  refreshToken?: string
  tokens?: Partial<AuthTokens>
}

export interface AuthResult {
  user: User
  tokens: AuthTokens
  session: Session | null
}
