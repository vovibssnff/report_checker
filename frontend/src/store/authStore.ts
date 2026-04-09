import { makeAutoObservable, runInAction } from 'mobx';
import type { User } from '../types/user';
import type { DevLoginPayload, DevRegisterPayload } from '../types/user';
import * as authApi from '../api/authApi';

export class AuthStore {
  user: User | null = null;
  authMode: 'dev' | 'itmo_id' = 'dev';
  loading = false;
  error: string | null = null;
  initialized = false;

  constructor() {
    makeAutoObservable(this);
  }

  get isAuthenticated(): boolean {
    return !!this.user;
  }

  setUser = (user: User | null) => {
    this.user = user;
  };

  login = async (payload: DevLoginPayload) => {
    this.loading = true;
    this.error = null;
    try {
      const user = await authApi.devLogin(payload);
      runInAction(() => {
        this.user = user;
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

  register = async (payload: DevRegisterPayload) => {
    this.loading = true;
    this.error = null;
    try {
      const user = await authApi.devRegister(payload);
      runInAction(() => {
        this.user = user;
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
    this.loading = true;
    try {
      const user = await authApi.fetchMe();
      runInAction(() => {
        this.user = user;
        this.loading = false;
        this.initialized = true;
      });
    } catch {
      runInAction(() => {
        this.user = null;
        this.loading = false;
        this.initialized = true;
      });
    }
  };

  logout = async () => {
    this.error = null;
    this.loading = true;
    try {
      await authApi.logout();
    } finally {
      runInAction(() => {
        this.user = null;
        this.loading = false;
      });
    }
  };

  fetchAuthMode = async () => {
    try {
      const mode = await authApi.getAuthMode();
      runInAction(() => {
        this.authMode = mode;
      });
    } catch {
      // Keep default mode for resilience in local dev.
    }
  };

  loginWithItmo = async () => {
    this.error = null;
    this.loading = true;
    try {
      const redirectUrl = await authApi.getLoginUrl();
      window.location.href = redirectUrl;
    } catch (e) {
      runInAction(() => {
        this.error = e instanceof Error ? e.message : 'ITMO ID login failed';
        this.loading = false;
      });
      throw e;
    }
  };
}

export const authStore = new AuthStore();
