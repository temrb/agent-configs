module RedirectPolicy
  def self.safe_path(value)
    return "/account" unless value&.start_with?("/")

    value
  end
end
