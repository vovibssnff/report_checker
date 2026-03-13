import { makeAutoObservable, runInAction } from 'mobx';
import type { User } from '../types/user';
import type { LoginPayload, RegisterPayload } from '../types/user';
import * as authApi from '../api/authApi';
import { clearStoredRefreshToken, clearStoredToken, getStoredToken, setStoredRefreshToken, setStoredToken } from '../api/client';

export class AuthStore {
  user: User | null = null;
  loading = false;
  error: string | null = null;

  constructor() {
    makeAutoObservable(this);
  }

  get isAuthenticated(): boolean {
    return !!this.user;
  }

  setUser = (user: User | null) => {
    this.user = user;
  };

  login = async (payload: LoginPayload) => {
    this.loading = true;
    this.error = null;
    try {
      const res = await authApi.login(payload);
      setStoredToken(res.access_token);
      setStoredRefreshToken(res.refresh_token);
      runInAction(() => {
        this.user = res.user;
        this.loading = false;
      });
    } catch (e) {
      runInAction(() => {
        this.error = e instanceof Error ? e.message : 'Login failed';
        this.loading = false;
      });
      throw e;
    }
  };

  register = async (payload: RegisterPayload) => {
    this.loading = true;
    this.error = null;
    try {
      const res = await authApi.register(payload);
      if (res.access_token) {
        setStoredToken(res.access_token);
        if (res.refresh_token) setStoredRefreshToken(res.refresh_token);
      }
      runInAction(() => {
        this.user = res.user;
        this.loading = false;
      });
    } catch (e) {
      runInAction(() => {
        this.error = e instanceof Error ? e.message : 'Registration failed';
        this.loading = false;
      });
      throw e;
    }
  };

  fetchMe = async () => {
    if (!getStoredToken()) {
      runInAction(() => { this.user = null; });
      return;
    }
    this.loading = true;
    try {
      const user = await authApi.fetchMe();
      runInAction(() => {
        this.user = user;
        this.loading = false;
      });
    } catch {
      runInAction(() => {
        this.user = null;
        this.loading = false;
      });
      clearStoredToken();
      clearStoredRefreshToken();
    }
  };

  logout = async () => {
    this.error = null;
    try {
      await authApi.logout();
    } finally {
      clearStoredToken();
      clearStoredRefreshToken();
      runInAction(() => {
        this.user = null;
      });
    }
  };
}

export const authStore = new AuthStore();
