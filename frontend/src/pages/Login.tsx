import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("instructor@kiu.edu.pk");
  const [password, setPassword] = useState("password123");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen">
      <section className="relative hidden w-[52%] overflow-hidden border-r border-border lg:block">
        <div
          className="absolute inset-0 bg-primary"
          style={{
            backgroundImage:
              "linear-gradient(160deg, hsl(160 48% 18%) 0%, hsl(160 40% 28%) 45%, hsl(42 40% 38%) 100%)",
          }}
        />
        <div className="relative flex h-full flex-col justify-between p-12 text-primary-foreground">
          <div className="flex items-center gap-3">
            <img
              src="/kiu_logo.png"
              alt="Karakoram International University"
              className="h-14 w-14 object-contain drop-shadow-sm"
            />
            <p className="text-sm uppercase tracking-[0.18em] text-primary-foreground/75">
              Karakoram International University
            </p>
          </div>
          <div className="max-w-md animate-fade-up">
            <h1 className="font-display text-5xl font-semibold leading-[1.1]">AutoScoring</h1>
            <p className="mt-4 text-lg text-primary-foreground/80">
              Grade subjective answers with semantic NLP — typed responses or photographed papers.
            </p>
          </div>
          <p className="text-sm text-primary-foreground/60">FYP · NLP &amp; Deep Learning</p>
        </div>
      </section>

      <section className="flex flex-1 items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm animate-fade-up">
          <div className="mb-8 flex items-center gap-3 lg:hidden">
            <img src="/kiu_logo.png" alt="" className="h-12 w-12 object-contain" aria-hidden />
            <div>
              <h1 className="font-display text-2xl font-semibold">AutoScoring</h1>
              <p className="text-sm text-muted-foreground">Instructor sign in</p>
            </div>
          </div>

          <h2 className="font-display text-3xl font-semibold">Welcome back</h2>
          <p className="mt-2 text-sm text-muted-foreground">Sign in to your instructor account</p>

          <form onSubmit={handleSubmit} className="mt-8 space-y-4">
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Signing in…" : "Sign in"}
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-muted-foreground">
            No account?{" "}
            <Link to="/register" className="font-medium text-primary hover:underline">
              Register
            </Link>
          </p>
          <p className="mt-3 text-center font-mono text-xs text-muted-foreground">
            Demo · instructor@kiu.edu.pk / password123
          </p>
        </div>
      </section>
    </div>
  );
}
