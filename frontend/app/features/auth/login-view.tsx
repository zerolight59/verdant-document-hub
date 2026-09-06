'use client';

import type { ComponentProps } from 'react';
import { ChevronRight, Network, ShieldCheck } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';


type LoginViewProps = {
  busy: boolean;
  error: string;
  onSubmit: ComponentProps<'form'>['onSubmit'];
};


export function LoginView({ busy, error, onSubmit }: LoginViewProps) {
  return (
    <main className="login-shell min-h-svh bg-[#0d2b20] text-white">
      <div className="login-grid min-h-svh">
        <section className="hidden min-h-svh flex-col justify-between p-12 lg:flex">
          <div className="flex items-center gap-3">
            <span className="flex size-11 items-center justify-center rounded-xl bg-[#c7f36b] text-[#153528]">
              <Network />
            </span>
            <div>
              <p className="font-semibold tracking-[.18em]">VERDANT</p>
              <p className="text-xs text-emerald-100/55">DOCUMENT HUB</p>
            </div>
          </div>
          <div className="max-w-xl">
            <p className="text-sm font-semibold uppercase tracking-[.15em] text-[#c7f36b]">
              Company knowledge, made visible
            </p>
            <h1 className="mt-5 text-5xl font-semibold leading-tight tracking-[-.04em]">
              Find the right document.
              <br />
              Know its exact status.
            </h1>
            <p className="mt-6 text-lg leading-8 text-emerald-50/65">
              Projects, responsibilities, reviews, versions, and research in
              one searchable workspace.
            </p>
          </div>
          <p className="text-sm text-emerald-100/40">
            Internal company system · Authorized employees only
          </p>
        </section>
        <section className="flex min-h-svh items-center justify-center bg-[#f4f7f5] px-5 text-slate-900 lg:rounded-l-[32px]">
          <form
            onSubmit={onSubmit}
            className="w-full max-w-md rounded-2xl border bg-white p-8 shadow-sm"
          >
            <p className="text-sm font-semibold text-emerald-700">
              Employee access
            </p>
            <h2 className="mt-2 text-3xl font-semibold">Sign in</h2>
            <p className="mt-2 text-sm text-slate-500">
              Your credentials are validated by Verdant&apos;s FastAPI and
              PostgreSQL backend.
            </p>
            <div className="mt-7 space-y-2">
              <Label htmlFor="employee-code">Employee ID or username</Label>
              <Input
                id="employee-code"
                name="employee_code"
                defaultValue="EMP-1042"
                autoComplete="username"
              />
            </div>
            <div className="mt-4 space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                name="password"
                type="password"
                defaultValue="verdant-demo"
                autoComplete="current-password"
              />
            </div>
            {error && (
              <p className="mt-3 text-sm text-rose-600" role="alert">
                {error}
              </p>
            )}
            <Button
              disabled={busy}
              className="mt-6 w-full bg-[#1b5e45] hover:bg-[#144b37]"
            >
              {busy ? 'Connecting…' : 'Sign in'} <ChevronRight />
            </Button>
            <div className="mt-5 flex gap-3 rounded-xl bg-emerald-50 p-4 text-sm text-emerald-900">
              <ShieldCheck className="size-5 shrink-0" />
              <span>Demo: EMP-1042 / verdant-demo</span>
            </div>
          </form>
        </section>
      </div>
    </main>
  );
}
