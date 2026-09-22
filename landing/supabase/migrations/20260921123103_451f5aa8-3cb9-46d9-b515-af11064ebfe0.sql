CREATE TABLE public.studio_inquiries (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL CHECK (char_length(name) BETWEEN 2 AND 120),
  email text NOT NULL CHECK (char_length(email) BETWEEN 5 AND 254),
  inquiry_type text NOT NULL CHECK (inquiry_type IN ('support', 'studio', 'press')),
  message text NOT NULL CHECK (char_length(message) BETWEEN 10 AND 3000),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
GRANT INSERT ON public.studio_inquiries TO anon, authenticated;
GRANT ALL ON public.studio_inquiries TO service_role;
ALTER TABLE public.studio_inquiries ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Anyone can submit a studio inquiry"
ON public.studio_inquiries
FOR INSERT
TO anon, authenticated
WITH CHECK (true);
CREATE OR REPLACE FUNCTION public.update_studio_inquiries_updated_at()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = public
AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;
CREATE TRIGGER studio_inquiries_updated_at
BEFORE UPDATE ON public.studio_inquiries
FOR EACH ROW
EXECUTE FUNCTION public.update_studio_inquiries_updated_at();