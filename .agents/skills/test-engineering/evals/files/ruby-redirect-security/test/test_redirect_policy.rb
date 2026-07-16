require "minitest/autorun"
require_relative "../lib/redirect_policy"

class RedirectPolicyTest < Minitest::Test
  def test_preserves_local_account_path
    assert_equal "/account/orders?open=1#latest", RedirectPolicy.safe_path("/account/orders?open=1#latest")
  end

  def test_uses_fallback_for_missing_value
    assert_equal "/account", RedirectPolicy.safe_path(nil)
  end
end
