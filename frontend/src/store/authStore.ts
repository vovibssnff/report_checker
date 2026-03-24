import { makeAutoObservable, runInAction } from 'mobx';
import type { User } from '../types/user';
import type { DevLoginPayload } from '../types/user';
import * as authApi from '../api/authApi';

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

  fetchMe = async () => {
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
}

export const authStore = new AuthStore();
