import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Search, Download, Star, TrendingUp, Filter } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface Template {
  template_id: string;
  name: string;
  description: string;
  category: string;
  industry: string;
  downloads: number;
  rating: number;
  reviews: number;
}

export default function Marketplace() {
  const { toast } = useToast();
  const [user, setUser] = useState<any>(null);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedIndustry, setSelectedIndustry] = useState<string>("all");
  const [sortBy, setSortBy] = useState<string>("downloads");
  const [viewMode, setViewMode] = useState<"grid" | "featured">("grid");

  const industries = ["all", "SaaS", "E-commerce", "Agency", "Healthcare", "Finance"];

  useEffect(() => {
    const user_id = localStorage.getItem("user_id");
    setUser({ id: user_id });
    fetchTemplates();
  }, []);

  useEffect(() => {
    fetchTemplates();
  }, [selectedIndustry, searchQuery, sortBy]);

  const fetchTemplates = async () => {
    setLoading(true);
    try {
      let url = "/api/marketplace/templates?";

      if (viewMode === "featured") {
        url += "featured_only=true";
      } else if (selectedIndustry !== "all") {
        url += `industry=${selectedIndustry}`;
      } else if (searchQuery) {
        url += `search=${encodeURIComponent(searchQuery)}`;
      }

      const response = await fetch(url);
      if (!response.ok) throw new Error("Failed to fetch templates");
      const data = await response.json();
      
      let sorted = Array.isArray(data) ? data : [];
      
      if (sortBy === "rating") {
        sorted.sort((a: any, b: any) => (b.rating || 0) - (a.rating || 0));
      } else if (sortBy === "newest") {
        sorted.reverse();
      } else {
        sorted.sort((a: any, b: any) => (b.downloads || 0) - (a.downloads || 0));
      }
      
      setTemplates(sorted);
    } catch (error) {
      console.error("Error fetching templates:", error);
      toast({
        title: "Error",
        description: "Failed to load templates",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (template_id: string) => {
    if (!user?.id) {
      toast({
        title: "Error",
        description: "Please sign in to download templates",
        variant: "destructive",
      });
      return;
    }

    try {
      const response = await fetch(`/api/marketplace/templates/${template_id}/download`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: user.id }),
      });

      if (!response.ok) throw new Error("Download failed");

      toast({
        title: "Success",
        description: "Template added to your workspace",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to download template",
        variant: "destructive",
      });
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 py-8">
      <div className="max-w-7xl mx-auto px-4">
        <h1 className="text-4xl font-bold text-white mb-2">Workflow Marketplace</h1>
        <p className="text-gray-400 mb-8">Explore 150+ pre-built templates for your industry</p>

        {/* Filters & Search */}
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 mb-8">
          <div className="grid md:grid-cols-4 gap-4">
            <div className="md:col-span-2">
              <Input
                placeholder="Search templates..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="bg-slate-700 border-slate-600 text-white"
              />
            </div>

            <Select value={selectedIndustry} onValueChange={setSelectedIndustry}>
              <SelectTrigger className="bg-slate-700 border-slate-600">
                <SelectValue placeholder="Select industry" />
              </SelectTrigger>
              <SelectContent>
                {industries.map((ind) => (
                  <SelectItem key={ind} value={ind}>
                    {ind === "all" ? "All Industries" : ind}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={sortBy} onValueChange={setSortBy}>
              <SelectTrigger className="bg-slate-700 border-slate-600">
                <SelectValue placeholder="Sort by" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="downloads">Most Popular</SelectItem>
                <SelectItem value="rating">Highest Rated</SelectItem>
                <SelectItem value="newest">Newest</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex gap-2 mt-4">
            <Button
              variant={viewMode === "grid" ? "default" : "outline"}
              onClick={() => setViewMode("grid")}
            >
              All Templates
            </Button>
            <Button
              variant={viewMode === "featured" ? "default" : "outline"}
              onClick={() => setViewMode("featured")}
            >
              <TrendingUp className="w-4 h-4 mr-2" />
              Featured
            </Button>
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="text-center py-12">
            <div className="text-white text-lg">Loading templates...</div>
          </div>
        )}

        {/* Templates Grid */}
        {!loading && templates.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-400 text-lg">No templates found. Try adjusting your filters.</p>
          </div>
        )}

        {!loading && templates.length > 0 && (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {templates.map((template) => (
              <Card key={template.template_id} className="bg-slate-800 border-slate-700 hover:border-purple-500 transition-colors">
                <CardHeader>
                  <div className="flex items-start justify-between mb-2">
                    <Badge variant="outline" className="text-xs">
                      {template.industry}
                    </Badge>
                    <div className="flex items-center gap-1">
                      <Star className="w-4 h-4 text-yellow-500 fill-current" />
                      <span className="text-sm text-white font-semibold">
                        {template.rating.toFixed(1)}
                      </span>
                    </div>
                  </div>
                  <CardTitle className="text-white text-lg">{template.name}</CardTitle>
                  <CardDescription className="text-gray-400 text-sm">
                    {template.description}
                  </CardDescription>
                </CardHeader>

                <CardContent>
                  <div className="space-y-4">
                    {/* Stats */}
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="bg-slate-700 p-2 rounded">
                        <div className="text-gray-400">Downloads</div>
                        <div className="text-white font-semibold">{template.downloads}</div>
                      </div>
                      <div className="bg-slate-700 p-2 rounded">
                        <div className="text-gray-400">Reviews</div>
                        <div className="text-white font-semibold">{template.reviews}</div>
                      </div>
                    </div>

                    {/* Tags */}
                    <div className="flex flex-wrap gap-1">
                      {template.category && (
                        <Badge variant="secondary" className="text-xs">
                          {template.category}
                        </Badge>
                      )}
                    </div>

                    {/* Action Button */}
                    <Button
                      onClick={() => handleDownload(template.template_id)}
                      className="w-full"
                      disabled={!user?.id}
                    >
                      <Download className="w-4 h-4 mr-2" />
                      Use Template
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Industry Showcase */}
        {!searchQuery && selectedIndustry === "all" && (
          <div className="mt-16">
            <h2 className="text-2xl font-bold text-white mb-8">Browse by Industry</h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-5 gap-4">
              {industries.slice(1).map((industry) => (
                <button
                  key={industry}
                  onClick={() => setSelectedIndustry(industry)}
                  className="p-6 bg-gradient-to-br from-slate-800 to-slate-700 border border-slate-600 rounded-lg hover:border-purple-500 transition-all text-white text-center font-semibold"
                >
                  {industry}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
