export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  // Allows to automatically instantiate createClient with right options
  // instead of createClient<Database, { PostgrestVersion: 'XX' }>(URL, KEY)
  __InternalSupabase: {
    PostgrestVersion: "14.1"
  }
  public: {
    Tables: {
      credentials: {
        Row: {
          created_at: string
          encrypted_access_token: string | null
          encrypted_api_key: string | null
          encrypted_refresh_token: string | null
          id: string
          metadata: Json | null
          provider_id: string
          token_expires_at: string | null
          type: Database["public"]["Enums"]["auth_type"]
          updated_at: string
          user_id: string
        }
        Insert: {
          created_at?: string
          encrypted_access_token?: string | null
          encrypted_api_key?: string | null
          encrypted_refresh_token?: string | null
          id?: string
          metadata?: Json | null
          provider_id: string
          token_expires_at?: string | null
          type: Database["public"]["Enums"]["auth_type"]
          updated_at?: string
          user_id: string
        }
        Update: {
          created_at?: string
          encrypted_access_token?: string | null
          encrypted_api_key?: string | null
          encrypted_refresh_token?: string | null
          id?: string
          metadata?: Json | null
          provider_id?: string
          token_expires_at?: string | null
          type?: Database["public"]["Enums"]["auth_type"]
          updated_at?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "credentials_provider_id_fkey"
            columns: ["provider_id"]
            isOneToOne: false
            referencedRelation: "providers"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "credentials_provider_id_fkey"
            columns: ["provider_id"]
            isOneToOne: false
            referencedRelation: "providers_public"
            referencedColumns: ["id"]
          },
        ]
      }
      execution_plans: {
        Row: {
          approved_at: string | null
          created_at: string
          id: string
          missing_auth: string[] | null
          name: string
          original_prompt: string
          plain_english_steps: string[] | null
          plan_json: Json
          required_providers: string[] | null
          status: Database["public"]["Enums"]["plan_status"]
          user_id: string
        }
        Insert: {
          approved_at?: string | null
          created_at?: string
          id?: string
          missing_auth?: string[] | null
          name: string
          original_prompt: string
          plain_english_steps?: string[] | null
          plan_json?: Json
          required_providers?: string[] | null
          status?: Database["public"]["Enums"]["plan_status"]
          user_id: string
        }
        Update: {
          approved_at?: string | null
          created_at?: string
          id?: string
          missing_auth?: string[] | null
          name?: string
          original_prompt?: string
          plain_english_steps?: string[] | null
          plan_json?: Json
          required_providers?: string[] | null
          status?: Database["public"]["Enums"]["plan_status"]
          user_id?: string
        }
        Relationships: []
      }
      executions: {
        Row: {
          error_message: string | null
          execution_plan_id: string
          finished_at: string | null
          id: string
          logs: Json[] | null
          started_at: string | null
          status: Database["public"]["Enums"]["execution_status"]
          user_id: string
        }
        Insert: {
          error_message?: string | null
          execution_plan_id: string
          finished_at?: string | null
          id?: string
          logs?: Json[] | null
          started_at?: string | null
          status?: Database["public"]["Enums"]["execution_status"]
          user_id: string
        }
        Update: {
          error_message?: string | null
          execution_plan_id?: string
          finished_at?: string | null
          id?: string
          logs?: Json[] | null
          started_at?: string | null
          status?: Database["public"]["Enums"]["execution_status"]
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "executions_execution_plan_id_fkey"
            columns: ["execution_plan_id"]
            isOneToOne: false
            referencedRelation: "execution_plans"
            referencedColumns: ["id"]
          },
        ]
      }
      providers: {
        Row: {
          actions: Json
          auth_type: Database["public"]["Enums"]["auth_type"]
          created_at: string
          display_name: string
          icon: string | null
          id: string
          name: string
          oauth_config: Json | null
        }
        Insert: {
          actions?: Json
          auth_type: Database["public"]["Enums"]["auth_type"]
          created_at?: string
          display_name: string
          icon?: string | null
          id?: string
          name: string
          oauth_config?: Json | null
        }
        Update: {
          actions?: Json
          auth_type?: Database["public"]["Enums"]["auth_type"]
          created_at?: string
          display_name?: string
          icon?: string | null
          id?: string
          name?: string
          oauth_config?: Json | null
        }
        Relationships: []
      }
    }
    Views: {
      providers_public: {
        Row: {
          actions: Json | null
          auth_type: Database["public"]["Enums"]["auth_type"] | null
          created_at: string | null
          display_name: string | null
          icon: string | null
          id: string | null
          name: string | null
        }
        Insert: {
          actions?: Json | null
          auth_type?: Database["public"]["Enums"]["auth_type"] | null
          created_at?: string | null
          display_name?: string | null
          icon?: string | null
          id?: string | null
          name?: string | null
        }
        Update: {
          actions?: Json | null
          auth_type?: Database["public"]["Enums"]["auth_type"] | null
          created_at?: string | null
          display_name?: string | null
          icon?: string | null
          id?: string | null
          name?: string | null
        }
        Relationships: []
      }
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      auth_type: "oauth" | "api_key"
      execution_status: "pending" | "running" | "success" | "failed"
      plan_status: "draft" | "approved" | "rejected"
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  public: {
    Enums: {
      auth_type: ["oauth", "api_key"],
      execution_status: ["pending", "running", "success", "failed"],
      plan_status: ["draft", "approved", "rejected"],
    },
  },
} as const
