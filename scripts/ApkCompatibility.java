import com.android.apksig.ApkVerifier;
import com.android.apksig.SigningCertificateLineage;
import java.io.File;
import java.security.MessageDigest;
import java.security.cert.X509Certificate;
import java.util.HexFormat;

/** Verify the signed lineage, rather than accepting a certificate printed in an untrusted file. */
public class ApkCompatibility {
    private static ApkVerifier.Result verified(String path, int sdk) throws Exception {
        var result = new ApkVerifier.Builder(new File(path))
                .setMinCheckedPlatformVersion(sdk).setMaxCheckedPlatformVersion(sdk).build().verify();
        if (!result.isVerified() || result.getSignerCertificates().size() != 1) {
            throw new IllegalArgumentException("APK signature invalid or multiple signers: " + path + " " + result.getAllErrors());
        }
        return result;
    }
    private static String digest(X509Certificate cert) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(cert.getEncoded()));
    }
    public static void main(String[] args) throws Exception {
        if (args.length != 3) throw new IllegalArgumentException("Usage: OLD_APK NEW_APK DEVICE_SDK");
        int sdk = Integer.parseInt(args[2]);
        if (sdk < 35) throw new IllegalArgumentException("This project requires Android SDK 35+");
        var oldResult = verified(args[0], sdk);
        var newResult = verified(args[1], sdk);
        var oldCert = oldResult.getSignerCertificates().get(0);
        var newCert = newResult.getSignerCertificates().get(0);
        boolean compatible = oldCert.equals(newCert);
        SigningCertificateLineage lineage = newResult.getSigningCertificateLineage();
        if (!compatible && lineage != null && lineage.isCertificateInLineage(oldCert)
                && lineage.isCertificateLatestInLineage(newCert)) {
            compatible = lineage.getSignerCapabilities(oldCert).hasInstalledData();
        }
        if (!compatible) throw new IllegalArgumentException("Incompatible signing certificates; refusing update without data migration");
        System.out.println("Compatible: " + digest(oldCert) + " -> " + digest(newCert));
    }
}
