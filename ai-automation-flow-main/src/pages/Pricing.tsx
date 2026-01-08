import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Check, X } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface PricingPlan {
  tier: string;
  price: number;
  billing: string;
  description: string;
  features: string[];
  limits: Record<string, string | number>;
}

export default function PricingPage() {
  const { toast } = useToast();
  const [plans, setPlans] = useState<PricingPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentPlan, setCurrentPlan] = useState<string>("FREE");
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    fetchPricingPlans();
    // Get current user from auth
    const user_id = localStorage.getItem("user_id");
    setUser({ id: user_id });
  }, []);

  const fetchPricingPlans = async () => {
    try {
      const response = await fetch("/api/pricing/plans");
      if (!response.ok) throw new Error("Failed to fetch pricing plans");
      const data = await response.json();
      setPlans(Array.isArray(data) ? data : Object.values(data));
    } catch (error) {
      console.error("Error fetching pricing:", error);
      toast({
        title: "Error",
        description: "Failed to load pricing plans",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = async (plan: string) => {
    if (!user?.id) {
      toast({
        title: "Error",
        description: "Please sign in to upgrade",
        variant: "destructive",
      });
      return;
    }

    try {
      const response = await fetch("/api/pricing/plan/upgrade", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: user.id, plan }),
      });

      if (!response.ok) throw new Error("Upgrade failed");
      
      setCurrentPlan(plan);
      toast({
        title: "Success",
        description: `Upgraded to ${plan} plan`,
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to upgrade plan",
        variant: "destructive",
      });
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 flex items-center justify-center">
        <div className="text-white text-xl">Loading pricing plans...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-white mb-4">Simple, Transparent Pricing</h1>
          <p className="text-xl text-gray-400">Choose the perfect plan for your automation needs</p>
        </div>

        {/* Pricing Cards */}
        <div className="grid md:grid-cols-4 gap-8 mb-12">
          {plans.map((plan) => (
            <Card
              key={plan.tier}
              className={`${
                currentPlan === plan.tier
                  ? "ring-2 ring-purple-500 bg-slate-800 border-purple-500"
                  : "bg-slate-800 border-slate-700"
              } hover:border-purple-500 transition-all`}
            >
              <CardHeader>
                <CardTitle className="text-white">{plan.tier}</CardTitle>
                <CardDescription className="text-gray-400">{plan.description}</CardDescription>
                <div className="mt-4">
                  <span className="text-4xl font-bold text-white">${plan.price}</span>
                  <span className="text-gray-400 ml-2">{plan.billing}</span>
                </div>
              </CardHeader>

              <CardContent className="space-y-6">
                <Button
                  onClick={() => handleUpgrade(plan.tier)}
                  variant={currentPlan === plan.tier ? "default" : "outline"}
                  className="w-full"
                  disabled={currentPlan === plan.tier}
                >
                  {currentPlan === plan.tier ? "Current Plan" : "Upgrade"}
                </Button>

                {/* Features */}
                <div className="space-y-3">
                  <h4 className="font-semibold text-white text-sm">Features & Limits</h4>
                  {Object.entries(plan.limits).map(([key, value]) => (
                    <div key={key} className="flex items-center gap-2 text-sm text-gray-300">
                      <Check className="w-4 h-4 text-green-500" />
                      <span>
                        {key}: <span className="font-semibold text-white">{value}</span>
                      </span>
                    </div>
                  ))}
                </div>

                {/* Plan Features */}
                {plan.features.length > 0 && (
                  <div className="space-y-2 border-t border-slate-700 pt-4">
                    {plan.features.map((feature, idx) => (
                      <div key={idx} className="flex items-start gap-2">
                        <Check className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                        <span className="text-sm text-gray-300">{feature}</span>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Comparison Table */}
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white">Feature Comparison</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700">
                    <th className="text-left py-3 px-4 text-gray-400">Feature</th>
                    <th className="text-center py-3 px-4 text-white">Free</th>
                    <th className="text-center py-3 px-4 text-white">Pro</th>
                    <th className="text-center py-3 px-4 text-white">Business</th>
                    <th className="text-center py-3 px-4 text-white">Enterprise</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-slate-700">
                    <td className="py-3 px-4 text-gray-300">Workflows</td>
                    <td className="text-center text-white">3</td>
                    <td className="text-center text-white">100</td>
                    <td className="text-center text-white">500</td>
                    <td className="text-center text-white">Unlimited</td>
                  </tr>
                  <tr className="border-b border-slate-700">
                    <td className="py-3 px-4 text-gray-300">Monthly Executions</td>
                    <td className="text-center text-white">50</td>
                    <td className="text-center text-white">5K</td>
                    <td className="text-center text-white">50K</td>
                    <td className="text-center text-white">Unlimited</td>
                  </tr>
                  <tr className="border-b border-slate-700">
                    <td className="py-3 px-4 text-gray-300">Team Members</td>
                    <td className="text-center text-white">1</td>
                    <td className="text-center text-white">3</td>
                    <td className="text-center text-white">20</td>
                    <td className="text-center text-white">Unlimited</td>
                  </tr>
                  <tr className="border-b border-slate-700">
                    <td className="py-3 px-4 text-gray-300">Custom Code</td>
                    <td className="text-center"><X className="w-4 h-4 text-red-500 mx-auto" /></td>
                    <td className="text-center"><Check className="w-4 h-4 text-green-500 mx-auto" /></td>
                    <td className="text-center"><Check className="w-4 h-4 text-green-500 mx-auto" /></td>
                    <td className="text-center"><Check className="w-4 h-4 text-green-500 mx-auto" /></td>
                  </tr>
                  <tr className="border-b border-slate-700">
                    <td className="py-3 px-4 text-gray-300">API Access</td>
                    <td className="text-center"><X className="w-4 h-4 text-red-500 mx-auto" /></td>
                    <td className="text-center"><Check className="w-4 h-4 text-green-500 mx-auto" /></td>
                    <td className="text-center"><Check className="w-4 h-4 text-green-500 mx-auto" /></td>
                    <td className="text-center"><Check className="w-4 h-4 text-green-500 mx-auto" /></td>
                  </tr>
                  <tr>
                    <td className="py-3 px-4 text-gray-300">Priority Support</td>
                    <td className="text-center"><X className="w-4 h-4 text-red-500 mx-auto" /></td>
                    <td className="text-center"><X className="w-4 h-4 text-red-500 mx-auto" /></td>
                    <td className="text-center"><Check className="w-4 h-4 text-green-500 mx-auto" /></td>
                    <td className="text-center"><Check className="w-4 h-4 text-green-500 mx-auto" /></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* FAQ */}
        <div className="mt-12 max-w-3xl mx-auto">
          <h2 className="text-2xl font-bold text-white mb-6">Frequently Asked Questions</h2>
          <div className="space-y-4">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white text-base">Can I change plans anytime?</CardTitle>
              </CardHeader>
              <CardContent className="text-gray-300">
                Yes, you can upgrade or downgrade your plan at any time. Changes take effect immediately.
              </CardContent>
            </Card>
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white text-base">What happens if I exceed my quota?</CardTitle>
              </CardHeader>
              <CardContent className="text-gray-300">
                We'll notify you when you're approaching your limit. New executions will be blocked until you upgrade.
              </CardContent>
            </Card>
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white text-base">Is there a free trial?</CardTitle>
              </CardHeader>
              <CardContent className="text-gray-300">
                Yes! Our Free plan is fully functional. Start building immediately without a credit card.
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
